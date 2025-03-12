from http.server import HTTPServer, SimpleHTTPRequestHandler
import socket
import netifaces

def get_all_ips():
    ips = []
    interfaces = netifaces.interfaces()
    
    for interface in interfaces:
        addrs = netifaces.ifaddresses(interface)
        if netifaces.AF_INET in addrs:
            for addr in addrs[netifaces.AF_INET]:
                ips.append(addr['addr'])
    return ips

# Create custom handler that only serves our deployment files
class DeploymentHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/deploy.zip', '/setup.sh']:
            return SimpleHTTPRequestHandler.do_GET(self)
        self.send_error(403)

# Set up the server
server_address = ('0.0.0.0', 8000)
httpd = HTTPServer(server_address, DeploymentHandler)

print(f"\nServing deployment files. Try these URLs from the Vultr console:")
for ip in get_all_ips():
    print(f"\nTry URL set #{get_all_ips().index(ip) + 1}:")
    print(f"wget http://{ip}:8000/deploy.zip")
    print(f"wget http://{ip}:8000/setup.sh")

print("\nPress Ctrl+C to stop")
httpd.serve_forever() 