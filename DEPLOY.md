# Deployment

OpenCodelists is currently deployed to smallweb1.  Deployment is with fabric:

```
fab deploy
```

You will need to configure SSH agent forwarding in your `~/.ssh/config`, e.g.

    Host smallweb1.ebmdatalab.net
    ForwardAgent yes
    User <your user on smallweb1>


macOS users will need to configure their SSH Agent to add their key by default as per [GitHub's Docs](https://docs.github.com/en/github/authenticating-to-github/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent#adding-your-ssh-key-to-the-ssh-agent).

On the server, use `with_environment.sh` to run a management command in the virtual environment with the correct settings:

```
./with_environment.sh ./manage.py shell
```
