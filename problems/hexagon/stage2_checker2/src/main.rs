mod interval;
mod json;
mod geometry;
use geometry::{Geometry,Node};
use interval::I;
use json::Json;
use std::{fs,io::{self,Write,BufWriter},sync::{atomic::{AtomicUsize,Ordering},mpsc},thread,time::Instant};
#[derive(Clone,Copy,Debug)]
struct Rational{p:i64,q:i64}
impl Rational{
    fn parse(v:&Json)->Result<Self,String>{
        let s=match v{Json::String(s)|Json::Number(s)=>s,_=>return Err("expected rational string or integer".into())};
        let mut parts=s.split('/');let p=parts.next().unwrap().parse::<i64>().map_err(|_|format!("invalid rational {s}"))?;
        let q=parts.next().unwrap_or("1").parse::<i64>().map_err(|_|format!("invalid rational {s}"))?;
        if parts.next().is_some(){return Err(format!("invalid rational {s}"))}I::rational(p,q)?;
        Ok(if q<0{Self{p:-p,q:-q}}else{Self{p,q}})
    }
    fn le(self,b:Self)->bool{self.p as i128*b.q as i128<=b.p as i128*self.q as i128}
    fn interval(self)->I{I::rational(self.p,self.q).unwrap()}
}
fn read_cert(path:&str)->Result<Vec<[I;6]>,String>{
    let text=fs::read_to_string(path).map_err(|e|format!("{path}: {e}"))?;
    let root=json::parse(&text)?;
    let obj=match root{Json::Object(o)=>o,_=>return Err("certificate must be an object".into())};
    let rows=match obj.get("excused"){Some(Json::Array(a))=>a,_=>return Err("missing excused array".into())};
    if rows.len()!=742{return Err(format!("expected 742 excused boxes, got {}",rows.len()))}
    rows.iter().enumerate().map(|(k,row)|{
        let a=match row{Json::Array(a) if a.len()==6=>a,_=>return Err(format!("box {k}: expected six rationals"))};
        let r:Vec<_>=a.iter().map(Rational::parse).collect::<Result<_,_>>()?;
        for i in [0,2,4]{if !r[i].le(r[i+1]){return Err(format!("box {k}: reversed bounds"))}}
        if !(Rational{p:0,q:1}).le(r[4]) || !r[5].le(Rational{p:1,q:7}){return Err(format!("box {k}: u outside [0,1/7]"))}
        Ok(std::array::from_fn(|i|r[i].interval()))
    }).collect()
}
fn root(e:&[I;6],g:&Geometry)->Node{
    [I::new(e[0].lo,e[1].hi)-g.v,I::new(e[2].lo,e[3].hi)-g.h,I::new(e[4].lo.max(0.0),e[5].hi.min(1.0)),
     I::new(-g.v.hi,g.v.hi),I::new(-g.h.hi,g.h.hi),I::new(0.0,1.0),
     I::new(-g.v.hi,g.v.hi),I::new(-g.h.hi,g.h.hi),I::new(0.0,1.0)]
}
#[derive(Debug)]
struct ResultRow{k:usize,nodes:u64,pruned:[u64;4],unproved:u64,max_depth:u32,seconds:f64,first:Option<Node>}
impl ResultRow{
    fn line(&self)->String{
        let mut s=format!("{{\"k\":{},\"proved\":{},\"nodes\":{},\"pruned\":{{\"A\":{},\"B\":{},\"C\":{},\"D\":{}}},\"unproved\":{},\"max_depth\":{},\"seconds\":{:.6}",self.k,self.unproved==0,self.nodes,self.pruned[0],self.pruned[1],self.pruned[2],self.pruned[3],self.unproved,self.max_depth,self.seconds);
        if let Some(n)=self.first{s.push_str(",\"first_unproved\":[");for (i,v) in n.iter().enumerate(){if i>0{s.push(',')}s.push_str(&format!("[{:?},{:?}]",v.lo,v.hi));}s.push(']');}s.push('}');s
    }
}
fn solve(k:usize,n:Node,g:&Geometry,wu:f64,limit:u32)->ResultRow{
    let start=Instant::now();let mut r=ResultRow{k,nodes:0,pruned:[0;4],unproved:0,max_depth:0,seconds:0.0,first:None};let mut stack=vec![(n,0u32)];
    while let Some((n,depth))=stack.pop(){
        r.nodes+=1;r.max_depth=r.max_depth.max(depth);
        if let Some(reason)=g.prune(&n){r.pruned[reason]+=1;continue}
        if depth>limit{r.unproved+=1;r.first.get_or_insert(n);continue}
        let mut choice=None;let mut best=-1.0;
        for (i,v) in n.iter().enumerate(){let width=v.width()*if i%3==2{wu}else{1.0};
            let mid=v.lo+(v.hi-v.lo)*0.5;
            if mid>v.lo && mid<v.hi && width>best{best=width;choice=Some((i,mid));}
        }
        if let Some((i,mid))=choice{let mut left=n;let mut right=n;left[i].hi=mid;right[i].lo=mid;stack.push((right,depth+1));stack.push((left,depth+1));}
        else{r.unproved+=1;r.first.get_or_insert(n);}
    }
    r.seconds=start.elapsed().as_secs_f64();r
}
struct Options{cert:String,ks:Option<String>,threads:usize,wu:f64,depth:u32,lemma:bool,scale:f64,out:Option<String>}
fn options()->Result<Options,String>{
    let mut o=Options{cert:"../stage1_cert.json".into(),ks:None,threads:thread::available_parallelism().map_or(1,usize::from),wu:4.0,depth:60,lemma:true,scale:1.0,out:None};
    let mut args=std::env::args().skip(1);
    while let Some(a)=args.next(){
        if a=="--no-lemma"{o.lemma=false;continue}
        if a=="--help" || a=="-h"{println!("hexs2 --cert PATH [--k 0-741 | --k 5] [--threads N] [--wu 4] [--max-depth 60] [--no-lemma] [--side-scale 1.0] [--out results.jsonl]");std::process::exit(0)}
        let v=args.next().ok_or_else(||format!("missing value for {a}"))?;
        match a.as_str(){"--cert"=>o.cert=v,"--k"=>o.ks=Some(v),"--out"=>o.out=Some(v),"--threads"=>o.threads=v.parse().map_err(|_|"invalid threads")?,"--wu"=>o.wu=v.parse().map_err(|_|"invalid wu")?,"--max-depth"=>o.depth=v.parse().map_err(|_|"invalid max-depth")?,"--side-scale"=>o.scale=v.parse().map_err(|_|"invalid scale")?,_=>return Err(format!("unknown option {a}"))}
    }
    if o.threads==0 || !o.wu.is_finite() || o.wu<=0.0 || o.depth==u32::MAX{return Err("require threads > 0, finite wu > 0, max-depth < u32::MAX".into())}Ok(o)
}
fn selection(s:Option<&str>,len:usize)->Result<Vec<usize>,String>{
    let s=match s{Some(s)=>s,None=>return Ok((0..len).collect())};
    let (a,b)=s.split_once('-').unwrap_or((s,s));let a:usize=a.parse().map_err(|_|"invalid k")?;let b:usize=b.parse().map_err(|_|"invalid k")?;
    if a>b || b>=len{return Err("k range outside certificate".into())}Ok((a..=b).collect())
}
fn run()->Result<bool,String>{
    let o=options()?;let g=Geometry::new(o.scale,o.lemma)?;let boxes=read_cert(&o.cert)?;let ks=selection(o.ks.as_deref(),boxes.len())?;
    // Open output only after validating inputs. Worker completion order determines JSONL order.
    let mut out:Box<dyn Write>=match o.out{Some(ref p)=>Box::new(BufWriter::new(fs::File::create(p).map_err(|e|e.to_string())?)),None=>Box::new(BufWriter::new(io::stdout()))};
    let start=Instant::now();let queue=AtomicUsize::new(0);let (tx,rx)=mpsc::channel();let mut proved=0;let mut nodes=0u64;
    thread::scope(|scope|->Result<(),String>{
        for _ in 0..o.threads.min(ks.len()){
            let tx=tx.clone();let ks=&ks;let boxes=&boxes;let g=&g;let queue=&queue;let o=&o;
            scope.spawn(move||loop{let i=queue.fetch_add(1,Ordering::Relaxed);if i>=ks.len(){break}let k=ks[i];let r=solve(k,root(&boxes[k],g),g,o.wu,o.depth);if tx.send(r).is_err(){break}});
        }
        drop(tx);
        for r in rx{proved+=usize::from(r.unproved==0);nodes+=r.nodes;writeln!(out,"{}",r.line()).map_err(|e|e.to_string())?;out.flush().map_err(|e|e.to_string())?;}
        Ok(())
    })?;
    eprintln!("proved {proved} / {}, total nodes {nodes}, wall time {:.6} s",ks.len(),start.elapsed().as_secs_f64());Ok(proved==ks.len())
}
fn main(){match run(){Ok(true)=>(),Ok(false)=>std::process::exit(1),Err(e)=>{eprintln!("hexs2: {e}");std::process::exit(2)}}}
#[cfg(test)]mod tests;
