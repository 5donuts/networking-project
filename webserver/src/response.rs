//! Module to build HTTP responses

use std::collections::HashMap;

/// supported HTTP version
const VERSION: &'static str = "HTTP/1.1";

/// template for the body of an error response
const ERR_TEMPLATE: &'static str = r#"<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Error {CODE}</title>
</head>
<body>
    <h1>{CODE}</h1>
    <p>{MESSAGE}</p>
</body>
</html>"#;

/// template for the response body of a `GET /` request
const INDEX_TEMPLATE: &'static str = r#"<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Secret Black Site</title>
</head>
<body>
    <p>Your IP address is: {IP_ADDR}</p>
</body>
</html>
"#;

pub struct HttpResponse {
    status: Status,
    headers: HashMap<String, String>,
    body: String,
}

impl HttpResponse {
    /// Build a response with an HTML body
    /// describing the error.
    pub fn error(status: Status, headers: Option<HashMap<String, String>>) -> Self {
        // build the body from the template
        let body = ERR_TEMPLATE
            .replace("{CODE}", format!("{}", status.code()).as_str())
            .replace("{MESSAGE}", status.message());

        // add necessary headers for the response
        let mut headers = if let Some(headers) = headers {
            headers
        } else {
            HashMap::new()
        };
        headers.insert("Content-Type".into(), "text/html".into());
        headers.insert("Content-Length".into(), format!("{}", body.len()));

        Self {
            status,
            headers,
            body,
        }
    }

    /// Build a response for a `GET /` request with the
    /// IP address of the client.
    pub fn index(ip_addr: &str, headers: Option<HashMap<String, String>>) -> Self {
        // this is a `200 Ok` response
        let status = Status::Ok;

        // build the body from the template
        let body = ERR_TEMPLATE.replace("{IP_ADDR}", ip_addr);

        // add necessary headers for the response
        let mut headers = if let Some(headers) = headers {
            headers
        } else {
            HashMap::new()
        };
        headers.insert("Content-Type".into(), "text/html".into());
        headers.insert("Content-Length".into(), format!("{}", body.len()));

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
