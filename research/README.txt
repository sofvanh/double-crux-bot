# Notebooks
These notebooks were used for prompt engineering and testing purposes. 

## auto_double_crux.ipynb
simulates a conversation between two people and a bot

## interactive_double_crux.ipynb
allows for two people to use an interactive dialogue to interact with the bot


modifying the prompts:
- identify the participants as /{participant_a/} and /{participant_b/}
- the first row represents the names of the steps of the conversation
- rows in a column are the prompts for the step's substeps in sequential order
- WARNING: please keep the first step's name as 'Start' and the last step's name as 'Close discussion'
- you may manually modify the variable initial_instructions in the notebook to change the bot's behavior
e.g., "You are a CFAR instructor with expertise in double crux."
- you may also want to modify the 'description' fields under ChatbotAction and DiscussionFlow or the 'message' field at the DiscussionFlow decision step

Other WARNINGS:
- please re-run the cell containing the WebConsoleModel each new conversation
