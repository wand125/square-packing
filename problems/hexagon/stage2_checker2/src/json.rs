//! Small strict JSON parser; preserves number lexemes, never converts rationals through JSON floats.
use std::collections::BTreeMap;
#[derive(Debug)]
pub enum Json { Null, Bool, Number(String), String(String), Array(Vec<Json>), Object(BTreeMap<String,Json>) }
pub fn parse(s:&str)->Result<Json,String> {
    let mut p=Parser{s:s.as_bytes(),i:0}; let v=p.value(0)?; p.ws();
    if p.i!=p.s.len(){return Err(format!("trailing JSON at byte {}",p.i))} Ok(v)
}
struct Parser<'a>{s:&'a [u8],i:usize}
impl Parser<'_>{
    fn ws(&mut self){while self.i<self.s.len() && matches!(self.s[self.i],b' '|b'\n'|b'\r'|b'\t'){self.i+=1;}}
    fn take(&mut self,c:u8)->bool {self.ws();if self.s.get(self.i)==Some(&c){self.i+=1;true}else{false}}
    fn need(&mut self,c:u8)->Result<(),String>{if self.take(c){Ok(())}else{Err(format!("expected {} at {}",c as char,self.i))}}
    fn string(&mut self)->Result<String,String>{
        self.need(b'"')?; let mut out=String::new();
        loop {let c=*self.s.get(self.i).ok_or("unterminated string")?;self.i+=1;
            match c {b'"'=>return Ok(out),b'\\'=>{
                let e=*self.s.get(self.i).ok_or("unterminated escape")?;self.i+=1;
                match e {b'"'=>out.push('"'),b'\\'=>out.push('\\'),b'/'=>out.push('/'),b'b'=>out.push('\u{8}'),b'f'=>out.push('\u{c}'),b'n'=>out.push('\n'),b'r'=>out.push('\r'),b't'=>out.push('\t'),b'u'=>{
                    let a=self.hex4()?;let cp=if (0xd800..=0xdbff).contains(&a){
                        if self.s.get(self.i..self.i+2)!=Some(b"\\u"){return Err("missing low surrogate".into())}self.i+=2;
                        let b=self.hex4()?;if !(0xdc00..=0xdfff).contains(&b){return Err("bad low surrogate".into())}0x10000+((a-0xd800)<<10)+(b-0xdc00)
                    }else{a};out.push(char::from_u32(cp).ok_or("invalid unicode")?);
                },_=>return Err("invalid escape".into())}
            },0..=31=>return Err("control character in string".into()),32..=127=>out.push(c as char),_=>{
                self.i-=1;let rest=std::str::from_utf8(&self.s[self.i..]).map_err(|_|"bad UTF-8")?;let ch=rest.chars().next().unwrap();self.i+=ch.len_utf8();out.push(ch);
            }}
        }
    }
    fn hex4(&mut self)->Result<u32,String>{let mut a=0;for _ in 0..4{let c=*self.s.get(self.i).ok_or("short unicode escape")?;self.i+=1;a=a*16+(c as char).to_digit(16).ok_or("bad unicode escape")?;}Ok(a)}
    fn value(&mut self,depth:usize)->Result<Json,String>{
        if depth>128{return Err("JSON nesting too deep".into())}self.ws();
        match self.s.get(self.i).copied().ok_or("missing JSON value")?{
            b'"'=>Ok(Json::String(self.string()?)),b'['=>{self.i+=1;let mut v=Vec::new();if self.take(b']'){return Ok(Json::Array(v))}loop{v.push(self.value(depth+1)?);if self.take(b']'){break}self.need(b',')?;}Ok(Json::Array(v))},
            b'{'=>{self.i+=1;let mut v=BTreeMap::new();if self.take(b'}'){return Ok(Json::Object(v))}loop{let key=self.string()?;self.need(b':')?;if v.insert(key,self.value(depth+1)?).is_some(){return Err("duplicate JSON key".into())}if self.take(b'}'){break}self.need(b',')?;}Ok(Json::Object(v))},
            b'n'|b't'|b'f'=>{let (word,v)=match self.s[self.i]{b'n'=>("null",Json::Null),b't'=>("true",Json::Bool),_=>("false",Json::Bool)};if !self.s[self.i..].starts_with(word.as_bytes()){return Err("bad literal".into())}self.i+=word.len();Ok(v)},
            b'-'|b'0'..=b'9'=>{let start=self.i;if self.s[self.i]==b'-'{self.i+=1;}
                match self.s.get(self.i){Some(b'0')=>self.i+=1,Some(b'1'..=b'9')=>{while matches!(self.s.get(self.i),Some(b'0'..=b'9')){self.i+=1;}},_=>return Err("bad number".into())}
                if self.s.get(self.i)==Some(&b'.'){self.i+=1;let p=self.i;while matches!(self.s.get(self.i),Some(b'0'..=b'9')){self.i+=1;}if self.i==p{return Err("bad fraction".into())}}
                if matches!(self.s.get(self.i),Some(b'e'|b'E')){self.i+=1;if matches!(self.s.get(self.i),Some(b'+'|b'-')){self.i+=1;}let p=self.i;while matches!(self.s.get(self.i),Some(b'0'..=b'9')){self.i+=1;}if self.i==p{return Err("bad exponent".into())}}
                Ok(Json::Number(std::str::from_utf8(&self.s[start..self.i]).unwrap().into()))
            },_=>Err(format!("bad JSON value at {}",self.i))
        }
    }
}
