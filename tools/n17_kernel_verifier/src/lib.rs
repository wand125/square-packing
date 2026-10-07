#![forbid(unsafe_code)]
pub mod exact;
pub mod geom;
pub mod int;
pub mod pyjson;
pub mod pyrandom;
pub mod stream;
pub mod sweep;
mod unicode_repr;
pub mod value;
pub mod verify;

pub type Result<T> = std::result::Result<T, Error>;
#[derive(Debug, Clone)]
pub enum Error {
    Check(String),
    UnicodeCheck(Vec<u32>),
    Malformed(String),
}
impl std::fmt::Display for Error {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Check(s) => f.write_str(s),
            Self::UnicodeCheck(s) => f.write_str(&pyjson::escape_points(s.iter().copied())),
            Self::Malformed(s) => write!(f, "malformed certificate: {s}"),
        }
    }
}
impl std::error::Error for Error {}
pub fn malformed(s: impl Into<String>) -> Error {
    Error::Malformed(s.into())
}
pub fn require(b: bool, s: impl Into<String>) -> Result<()> {
    if b {
        Ok(())
    } else {
        Err(Error::Check(s.into()))
    }
}
impl From<std::io::Error> for Error {
    fn from(e: std::io::Error) -> Self {
        malformed(e.to_string())
    }
}
impl From<serde_json::Error> for Error {
    fn from(e: serde_json::Error) -> Self {
        malformed(e.to_string())
    }
}

#[cfg(test)]
mod tests;

impl Error {
    pub fn receipt_value(&self) -> value::Value {
        match self {
            Self::UnicodeCheck(s) => value::Value::string(s.clone()),
            _ => value::Value::String(self.to_string()),
        }
    }
}
