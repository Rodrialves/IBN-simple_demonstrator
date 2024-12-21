from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel

def simple_topology():
    """Create a simple Mininet topology with a remote controller."""

    # Set up the Mininet instance
    net = Mininet()

    # Add a remote controller (update IP and port as needed)
    controller = net.addController('c0',
                                    controller=RemoteController,
                                    ip='127.0.0.1',  # Replace with your controller's IP
                                    port=6653)       # Default OpenFlow port

    # Add a switch
    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')

    # Add hosts
    h1 = net.addHost('h1', ip='10.0.0.1')
    h2 = net.addHost('h2', ip='10.0.0.2')
    h3 = net.addHost('h3', ip='10.0.0.3')
    h4 = net.addHost('h4', ip='10.0.1.1')

    # Create links between the switch and the hosts
    net.addLink(s1, h1)
    net.addLink(s1, h2)
    net.addLink(s1, h3)
    net.addLink(s2, h4)
    net.addLink(s1, s2)

    # Start the network
    net.start()

    print("Topology is up. Use the CLI to test connectivity.")

    # Start the CLI for user interaction
    CLI(net)

    # Stop the network
    net.stop()

if __name__ == '__main__':
    # Set Mininet log level to info
    setLogLevel('info')

    # Start the topology
    simple_topology()

