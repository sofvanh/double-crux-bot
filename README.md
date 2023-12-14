# Double Crux Bot

Bot that facilitates double crux sessions to help participants resolve disagreements. Currently implemented to work as a Slack app, Discord support incoming. 

The repo is currently setup for hosting on Heroku. Slack workspace tokens are expected to be stored in a Postgres database. Run locally with `ngrok http 3000` + `python app.py` in the `app` folder. Run tests by running `python -m unittest discover tests` in root folder. Remember to set the required environment variables.

AI logic makes heavy use of [Interlab by ACS research](https://github.com/acsresearch/interlab).