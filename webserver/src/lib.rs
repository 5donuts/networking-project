//! A toy implementation of a webserver based on the implementation
//! from The Book.

mod request;
mod response;

use log::info;
use request::HttpRequest;
use response::HttpResponse;
use std::convert::TryFrom;
use std::io::prelude::*;
use std::net::{TcpListener, TcpStream};
use threadpool::ThreadPool;

pub struct Server {
    listener: TcpListener,
    pool: ThreadPool,
}

impl Server {
    /// Initialize the server.
    ///
    /// # Arguments
    /// * `bind_addr` - The address (and port) at which to listen for TCP connections
    /// * `threads` - The number of threads to use to process requests.
    ///
    /// # Panics
    /// `init` will panic if `threads` is zero.
    pub fn init(bind_addr: &str, threads: usize) -> Self {
        // setup the listener and thread pool
        let listener = TcpListener::bind(bind_addr).expect("Unable to bind to address.");
        let pool = ThreadPool::new(threads);

        // in case the port '0' (use a random port) was specified in the bind addr,
        // get the address the listener is on, then log that information
        let addr = listener.local_addr().unwrap();
        info!(
            "Started server at addr: {} with {} threads.",
            &addr.to_string(),
            threads
        );

        Self { listener, pool }
    }

    pub fn start(&self) {
        for stream in self.listener.incoming() {
            let stream = stream.unwrap();
            self.pool.execute(|| process_connection(stream));
        }
    }
}

fn process_connection(mut stream: TcpStream) {
    let mut buffer = [0; 1024];
    stream.read(&mut buffer).unwrap();
    let req = String::from_utf8_lossy(&buffer[..]).into_owned();

    let response = if let Ok(req) = HttpRequest::try_from(req.as_str()) {
        // ensure the request version is supported
        if req.version() != "HTTP/1.1" {
            info!(
                "Got request for unsupported HTTP version: {}",
                req.version()
            );
            HttpResponse::error(response::Status::BadRequest, None)
        }
        // ensure the request is for a supported endpoint
        else if req.path() != "/" {
            info!("Got request for invalid path: {}", req.path());
            HttpResponse::error(response::Status::NotFound, None)
        }
        // the request is (probably) valid, we just might not respect
        // the headers it has (since we never check)
        else {
            let ip = "foo bar baz";
            HttpResponse::index(ip, None)
        }
    } else {
        // TODO: handle the case where the request is for an unsupported
        // method (that should get a NotImplemented response instead).
        info!("Got bad request: {}", req);
        HttpResponse::error(response::Status::BadRequest, None)
    };

    stream.write(response.to_string().as_bytes()).unwrap();
    stream.flush().unwrap();
}
