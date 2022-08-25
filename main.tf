terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

provider "digitalocean" {
  token = "1c6508e264c30fcc6249f937d2d4eb2cacd6ebbf25b1b7cd300b777cb2339195"
}

resource "digitalocean_droplet" "server" {
  image     = "debian-11-x64"
  name      = "dhdb-us-housing-prices-v2"
  region    = "sfo3"
  size      = "s-8vcpu-16gb"
  ssh_keys  = ["a0:39:2b:6a:4b:25:55:64:8a:d6:4c:80:05:69:3c:1b"]
  user_data = file("provision.sh")

  connection {
    host        = self.ipv4_address
    user        = "root"
    type        = "ssh"
    timeout     = "2m"
    private_key = file("~/.ssh/id_ed25519")
  }

  provisioner "file" {
    source      = "~/.dolt"
    destination = "/root"
  }
}

output "server_ip" {
  value = resource.digitalocean_droplet.server.ipv4_address
}

