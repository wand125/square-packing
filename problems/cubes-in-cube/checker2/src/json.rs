use std::collections::BTreeMap;
#[derive(Clone, Debug)]
pub enum J {
    Num(f64, String),
    Str(String),
    Arr(Vec<J>),
    Obj(BTreeMap<String, J>),
    Bool,
    Null,
}
impl J {
    pub fn num(&self) -> f64 {
        if let J::Num(v, _) = self {
            *v
        } else {
            panic!("expected number")
        }
    }
    pub fn uint(&self) -> u64 {
        if let J::Num(_, text) = self { text.parse().expect("expected exact unsigned integer") } else { panic!("expected integer") }
    }
    pub fn str(&self) -> &str {
        if let J::Str(v) = self {
            v
        } else {
            panic!("expected string")
        }
    }
    pub fn arr(&self) -> &[J] {
        if let J::Arr(v) = self {
            v
        } else {
            panic!("expected array")
        }
    }
    pub fn get(&self, k: &str) -> &J {
        if let J::Obj(v) = self {
            v.get(k).expect(k)
        } else {
            panic!("expected object")
        }
    }
}
pub fn parse(s: &str) -> J {
    struct P<'a> {
        s: &'a [u8],
        i: usize,
    }
    impl P<'_> {
        fn ws(&mut self) {
            while self.i < self.s.len() && self.s[self.i].is_ascii_whitespace() {
                self.i += 1;
            }
        }
        fn eat(&mut self, b: u8) {
            self.ws();
            assert_eq!(self.s[self.i], b);
            self.i += 1;
        }
        fn val(&mut self) -> J {
            self.ws();
            match self.s[self.i] {
                b'[' => {
                    self.i += 1;
                    let mut v = vec![];
                    self.ws();
                    if self.s[self.i] != b']' {
                        loop {
                            v.push(self.val());
                            self.ws();
                            if self.s[self.i] != b',' {
                                break;
                            }
                            self.i += 1;
                        }
                    }
                    self.eat(b']');
                    J::Arr(v)
                }
                b'{' => {
                    self.i += 1;
                    let mut v = BTreeMap::new();
                    self.ws();
                    if self.s[self.i] != b'}' {
                        loop {
                            let k = self.val().str().to_string();
                            self.eat(b':');
                            assert!(v.insert(k, self.val()).is_none());
                            self.ws();
                            if self.s[self.i] != b',' {
                                break;
                            }
                            self.i += 1;
                        }
                    }
                    self.eat(b'}');
                    J::Obj(v)
                }
                b'"' => {
                    self.i += 1;
                    let start = self.i;
                    while self.s[self.i] != b'"' {
                        assert!(self.s[self.i] != b'\\');
                        self.i += 1;
                    }
                    let v = std::str::from_utf8(&self.s[start..self.i])
                        .unwrap()
                        .to_string();
                    self.i += 1;
                    J::Str(v)
                }
                b'n' => {
                    assert_eq!(&self.s[self.i..self.i + 4], b"null");
                    self.i += 4;
                    J::Null
                }
                b't' => {
                    assert_eq!(&self.s[self.i..self.i + 4], b"true");
                    self.i += 4;
                    J::Bool
                }
                b'f' => {
                    assert_eq!(&self.s[self.i..self.i + 5], b"false");
                    self.i += 5;
                    J::Bool
                }
                _ => {
                    let start = self.i;
                    while self.i < self.s.len()
                        && (self.s[self.i].is_ascii_digit() || b"+-.eE".contains(&self.s[self.i]))
                    {
                        self.i += 1;
                    }
                    let x = std::str::from_utf8(&self.s[start..self.i])
                        .unwrap()
                        .parse::<f64>()
                        .unwrap();
                    assert!(x.is_finite());
                    J::Num(x, std::str::from_utf8(&self.s[start..self.i]).unwrap().to_string())
                }
            }
        }
    }
    let mut p = P {
        s: s.as_bytes(),
        i: 0,
    };
    let j = p.val();
    p.ws();
    assert_eq!(p.i, p.s.len());
    j
}
