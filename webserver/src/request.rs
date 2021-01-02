//! Module to parse HTTP requests

use std::{collections::HashMap, convert::TryFrom};

use log::trace;

#[derive(Debug)]
pub struct HttpRequest<'a> {
    method: Method,
    path: &'a str,
    version: &'a str,
    headers: HashMap<&'a str, String>,
}

impl<'a> TryFrom<&'a str> for HttpRequest<'a> {
    type Error = &'static str;

    fn try_from(s: &'a str) -> Result<Self, Self::Error> {
        trace!("Parsing request: {}", s);

        let mut lines = s.split_terminator("\r\n");
        let mut req = lines
            .next()
            .ok_or("Error getting first line of request.")?
            .split_terminator(" ");

        let method = req.next().ok_or("Error getting request method.")?;
        let path = req.next().ok_or("Error getting request path.")?;
        let version = req.next().ok_or("Error getting request HTTP version.")?;
        let mut headers = HashMap::new();

        for s in lines.into_iter().filter(|l| l.contains(": ")) {
            let mut parts = s.split_terminator(": ");
            let header = parts.next().ok_or("Error getting header key.")?;
            let val = parts.collect::<Vec<&str>>().join(": ");
            headers.insert(header, val);
        }

        trace!(
            "Parsed request:\n\tmethod: {}\n\tpath: {}\n\tversion: {}\n\theaders: {:?}",
            method,
            path,
            version,
            headers
        );

        Ok(Self {
            method: method.into(),
            path,
            version,
            headers,
        })
    }
}

#[derive(Debug)]
enum Method {
    Get,
    Head,
    Unsupported,
}

impl From<&str> for Method {
    fn from(s: &str) -> Self {
        match s.to_uppercase().as_str() {
            "GET" => Method::Get,
            "HEAD" => Method::Head,
            _ => Method::Unsupported,
        }
    }
}
