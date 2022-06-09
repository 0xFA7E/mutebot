# mutebot
discord bot that mutes people based on the rate of typing and the phase of the moon

## Config

### Bot Configuration
Bot configuration is done with a .env file loaded with the discord bot token

```
DISCORD=<BOT TOKEN HERE>
```

### Target Configuration

Target configuration is done in a config.json file with the format of:

```json
{"users": [], "roles": []}
```

Fill in predetermined user IDs in the users [] bracket, and role IDs in the roles [] bracket. User IDs can be found by enabling dev mode in discord
and right clicking a users name and selecting copy ID. Role IDs can be obtained by tagging a role with a backslash \@role The ID will be between the <>.


## Permissions
mutebot only requires the Manage Messages permission to function
