# SDN Link Manager Demonstrator

This project demonstrates SDN capabilities using the Ryu controller and Mininet. The tool allows users to dynamically manage (block/unblock) the connection between two switches (`s1` and `s2`) using a REST API and a simple CLI interface.

---

## Prerequisites

Before you begin, make sure the following are installed:

1. **Mininet**:
   ```bash
   sudo apt-get install mininet
   ```
2. **Ryu Controller**:
   ```bash
   pip install ryu
   ```
3. **Python 3.9**

---

## Project Files

- **`link_manager.py`**: The Ryu application to manage the link between `s1` and `s2`.
- **`simple_topology.py`**: Mininet script to set up the network topology.
- **`intent_cli.py`**: A simple CLI to block or unblock the link using REST API calls.

---

## How to Run the Project

### Step 1: Start the Ryu Controller
Open a terminal and run the Ryu application:
```bash
ryu-manager link_manager.py
```

This starts the Ryu controller and initializes the REST API for link management.

### Step 2: Launch the Mininet Topology
Open a new terminal and run the Mininet topology script:
```bash
sudo python3 simple_topology.py
```

This creates the network topology:
- Switches: `s1` and `s2`
- Hosts: `h1`, `h2`, `h3`, `h4`

### Step 3: Use the CLI Interface
In a third terminal, launch the CLI tool to interact with the controller:
```bash
python3 cli_interface.py
```

Follow the prompts to:
1. **Block the link**: Disables communication between `s1` and `s2`.
2. **Unblock the link**: Restores communication between `s1` and `s2`.

---

## Example Usage

### 1. Check Connectivity
After starting Mininet, test network connectivity:
```bash
mininet> pingall
```

### 2. Block the Link
Using the CLI interface:
- Choose the **Block** option to disable the link.

Alternatively, use `curl`:
```bash
curl -X POST http://127.0.0.1:8080/link/down
```

### 3. Test Connectivity Again
Run `pingall` in Mininet to observe that the link between `s1` and `s2` is blocked:
```bash
mininet> pingall
```

### 4. Unblock the Link
Using the CLI interface:
- Choose the **Unblock** option to re-enable the link.

Alternatively, use `curl`:
```bash
curl -X POST http://127.0.0.1:8080/link/up
```

Run `pingall` again to confirm that connectivity is restored:
```bash
mininet> pingall
```

---

## Troubleshooting

1. **Cleanup Mininet**: If you encounter errors when starting Mininet, clean up stale processes:
   ```bash
   sudo mn -c
   ```

2. **Check Controller Logs**: Ensure the Ryu controller is running without errors.

---

## License

This project is licensed under the MIT License.
