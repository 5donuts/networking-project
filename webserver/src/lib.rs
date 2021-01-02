//! A toy implementation of a webserver based on the implementation
//! from The Book.

mod request;
mod response;

use log::info;
use request::HttpRequest;
use response::HttpResponse;
use std::convert::TryFrom;
use std::fs;
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

    let response = if let Ok(req) =
        HttpRequest::try_from(String::from_utf8_lossy(&buffer[..]).into_owned().as_str())
    {
        todo!("process the request");
    } else {
        let status = response::Status::BadRequest;
        let body = fs::read_to_string("pages/error.html")
            .expect("Unable to read error page template")
            .replace("{CODE}", format!("{}", status.code()).as_str())
            .replace("{MESSAGE}", status.message());
        HttpResponse::new(status, None, Some(body))
    };

    stream.write(response.to_string().as_bytes()).unwrap();
    stream.flush().unwrap();
}
