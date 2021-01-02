use webserver::Server;

fn main() {
    env_logger::init();

    // TODO set up command-line args for these
    let bind_addr = "127.0.0.1:7878";
    let threads = 4;

    let server = Server::init(bind_addr, threads);
    server.start();
}
