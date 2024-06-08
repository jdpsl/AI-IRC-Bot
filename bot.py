import socket
import openai

# Configuration
server = "your irc server hostname"
port = 6667
channel = "#ai_chat"
botnick = "AI"
api_key = "lm-studio"
model_identifier = "model-identifier"
base_url = "http://localhost:1234/v1"

# OpenAI setup
client = openai.OpenAI(api_key=api_key, base_url=base_url)

def create_openai_response(prompt):
    try:
        completion = client.chat.completions.create(
            model=model_identifier,
            messages=[
                {"role": "system", "content": "Be as helpful as possible."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating response: {e}"

# Connect to IRC server
irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
irc.connect((server, port))
irc.send(f"NICK {botnick}\r\n".encode("utf-8"))
irc.send(f"USER {botnick} 0 * :{botnick}\r\n".encode("utf-8"))
irc.send(f"JOIN {channel}\r\n".encode("utf-8"))

def send_message(message):
    irc.send(f"PRIVMSG {channel} :{message}\r\n".encode("utf-8"))

def send_multiline_message(message):
    lines = message.split('\n')
    for line in lines:
        send_message(line)

def handle_command(command, user):
    parts = command.split()
    cmd = parts[0].lower()
    
    if cmd == "op" and len(parts) > 1:
        target = parts[1]
        irc.send(f"MODE {channel} +o {target}\r\n".encode("utf-8"))
        send_message(f"{user} has given operator status to {target}.")
    elif cmd == "kick" and len(parts) > 1:
        target = parts[1]
        reason = " ".join(parts[2:]) if len(parts) > 2 else ""
        irc.send(f"KICK {channel} {target} :{reason}\r\n".encode("utf-8"))
        send_message(f"{user} has kicked {target}.")
    elif cmd == "ban" and len(parts) > 1:
        target = parts[1]
        irc.send(f"MODE {channel} +b {target}\r\n".encode("utf-8"))
        irc.send(f"KICK {channel} {target} :Banned\r\n".encode("utf-8"))
        send_message(f"{user} has banned {target}.")
    elif cmd == "join" and len(parts) > 1:
        new_channel = parts[1]
        irc.send(f"JOIN {new_channel}\r\n".encode("utf-8"))
        send_message(f"Joined channel {new_channel}.")
    else:
        send_message(f"Unknown command: {cmd}")

# Main loop
while True:
    try:
        ircmsg = irc.recv(2048)
        ircmsg = ircmsg.decode("utf-8", errors="ignore").strip("\n\r")
        print(ircmsg)  # Print IRC messages to console for debugging

        if "PING :" in ircmsg:
            irc.send(f"PONG :{ircmsg.split(':')[1]}\r\n".encode("utf-8"))

        if f"PRIVMSG {channel}" in ircmsg:
            user = ircmsg.split('!', 1)[0][1:]
            message = ircmsg.split(f"PRIVMSG {channel} :", 1)[1]
            
            if message.startswith("!"):
                command = message[1:].strip()
                if any(command.startswith(cmd) for cmd in ["op", "kick", "ban", "join"]):
                    handle_command(command, user)
                else:
                    response_prompt = command
                    response = create_openai_response(response_prompt)
                    send_multiline_message(f"{user}: {response}")
    except Exception as e:
        print(f"Error: {e}")
