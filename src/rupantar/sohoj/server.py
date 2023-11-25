from http.server import SimpleHTTPRequestHandler
from socket import SOL_SOCKET, SO_REUSEADDR
from socketserver import TCPServer
from os import path, chdir, getcwd
import random
import ipaddress
import logging
from rupantar.sohoj.configger import Config

logger = logging.getLogger()


def validate_network_address(interface_address):
    """Validate a given network address to check if it is a valid IP address.

    Link-local and multicast addresses are considered to be invalid.

    Note:
        The link-local addresses = reserved range of 169.254.1.0 to 169.254.254.255, as per the IETF.

    Args:
      interface_address: Network address to validate

    Returns:
        bool: True if the given network address is a valid, non-link-local, non-multicast IP address. False otherwise.

    """
    try:
        ip = ipaddress.ip_address(interface_address)
        if ip.is_link_local or ip.is_multicast:
            return False
        return True
    except ValueError:
        return False


def start_server(project_folder, config_file_name, port, interface_address):
    """Start a basic HTTP server to serve the static files of the project. Ideal for sampling the pages locally on any machine.

    Change the current working directory to the given project folder, reads and loads the configuration data,
    and starts an HTTP server at the given network address and port.
    The server then serves the static files generated by the project.


    Args:
        project_folder (str): The path to the rupantar project folder where the 'content' and 'notes' directories are located.
        config_file_name (str): The name of the configuration file. Defaults to config.yml if not explicitly provided.
        port (int): The port number to use for the server. If the port is None or in the range 0-1024, a random port in the range 49152-65535 is used as default.
        interface_address (str): The network address to use for the server. If the address is not valid, '127.0.0.1' i.e. localhost is used as default.

    Raises:
        Exception: If any error starting the HTTP server or while serving the files.

    """
    try:
        config_file = "config.yml" if (config_file_name is None) else config_file_name
        # Ephemeral/dynamic/private ports, think good for temporary stuff
        PORT = (
            random.randint(49152, 65535)
            if ((port is None) or ((port in range(0, 1024))))
            else port
        )
        logger.info("Using port: %s", PORT)
        HOST = (
            interface_address
            if (validate_network_address(interface_address))
            else "127.0.0.1"
        )
        logger.info("Using network address: %s", HOST)
        # Change cwd to project folder
        chdir(project_folder)
        curr_dir = getcwd()
        logger.info(f"cwd is now: {curr_dir}")
        project_folder_path = curr_dir
        logger.info("Rupantar project directory location: %s", project_folder_path)
        # Location of config file, assumed to be in abovementioned project folder
        config_file_path = path.join(project_folder_path, config_file)
        logger.info("Config file location: %s", config_file_path)
        # Instantiate Config object for reading and loading config data values
        config = Config(config_file_path)
        # Change cwd to folder from where generated static filed will be served (public/ for example)
        chdir(path.join(project_folder_path, config.home_path))
        logger.debug(
            "Current working directory: %s",
            path.abspath(path.expanduser(path.expandvars(path.curdir))),
        )  # https://stackoverflow.com/a/55034470
        try:
            with TCPServer((HOST, PORT), SimpleHTTPRequestHandler) as httpd:
                # Allow immediate socket re-use
                httpd.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
                print(f"HTTP server listening at http://{HOST}:{PORT}")
                httpd.serve_forever()
        except KeyboardInterrupt:
            print("Stopping server...")
            httpd.server_close()
        except Exception as err:
            logger.exception("Error while serving the server: %s", str(err))

    except Exception as err:
        logger.exception("Error starting server: %s", str(err))
