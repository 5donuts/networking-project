//! Module to build HTTP responses

use std::collections::HashMap;

const VERSION: &'static str = "HTTP/1.1";

pub struct HttpResponse {
    status: Status,
    headers: HashMap<String, String>,
    body: String,
}

impl HttpResponse {
    pub fn new(
        status: Status,
        headers: Option<HashMap<String, String>>,
        body: Option<String>,
    ) -> Self {
        let body = if let Some(body) = body {
            body
        } else {
            "".into()
        };
        let headers = if let Some(headers) = headers {
            let mut headers = headers;
            headers.insert("Content-Length".into(), format!("{}", body.len()));
            headers.insert("Content-Type".into(), "text/html".into());
            headers
        } else {
            HashMap::new()
        };

        Self {
            status,
            headers,
            body,
        }
    }

    pub fn to_string(&self) -> String {
        let mut lines = Vec::new();

        lines.push(format!(
            "{} {} {}\r",
            VERSION,
            self.status.code(),
            self.status.message()
        ));

        self.headers.iter().for_each(|(k, v)| {
            lines.push(format!("{}: {}\r", k, v));
        });

        lines.push(self.body.clone());

        lines.join("\n")
    }

    pub fn status(&self) -> &Status {
        &self.status
    }
}

pub enum Status {
    Ok,
    BadRequest,
    NotFound,
    InternalServerError,
    NotImplemented,
}

impl Status {
    pub fn code(&self) -> u16 {
        match self {
            Status::Ok => 200,
            Status::BadRequest => 400,
            Status::NotFound => 404,
            Status::InternalServerError => 500,
            Status::NotImplemented => 501,
        }
    }

    pub fn message(&self) -> &'static str {
        match self {
            Status::Ok => "Ok",
            Status::BadRequest => "Bad Request",
            Status::NotFound => "Not Found",
            Status::InternalServerError => "Internal Server Error",
            Status::NotImplemented => "Not Implemented",
        }
    }
}
