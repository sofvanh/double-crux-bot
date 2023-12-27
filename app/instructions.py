import csv
from enum import Enum
from aenum import extend_enum
from pydantic.dataclasses import dataclass, Field


def get_all_bot_instructions():
  bot_instructions = {}
  with open("bot_instructions.csv", encoding='utf-8-sig') as csvfile:
    dict_reader = csv.DictReader(csvfile, escapechar='\\')
    for row in dict_reader:
      for (key, value) in row.items():
        if value:
          if key not in bot_instructions:
            bot_instructions[key] = []
          bot_instructions[key].append(value)
  return bot_instructions


def get_bot_instruction(step, substep, name_a, name_b, optional_instructions = ''):
  return bot_instructions.get(step)[substep].format(participant_a = name_a, participant_b = name_b, optional_instructions = f' {optional_instructions}')


def get_initial_bot_instructions(name_a, name_b):
  initial_instructions = 'You are Harmony, a discussion facilitator using the applied rationality method Double Crux to help participants find \'cruxes\' upon which a disagreement hinges.\n\
  A crux for an individual is a fact that would change their conclusion in the overall disagreement.\n\
  A double-crux is two exactly opposite cruxes: One crux is a fact that, if true, disproves one participant\'s belief.\n\
  The second crux is the same exact fact that, if false, disproves the other participant\'s belief.\n\
  Here is the premise: {name_a} and {name_b} hold conflicting beliefs.\n\
  Your job is to discover a double-crux. First, find a crux such that if {name_a} believed the crux was true (or false), then they would change their mind about their belief.\n\
  Secondly, check if the opposite conclusion about that same crux would change {name_b}\'s mind. If so, then there is a double-crux.\n\
  Cruxes should be more concrete, falsifiable, well-defined, and/or discoverable than beliefs.\n\
  Double-crux discussions differ from typical debates which are usually adversarial, and instead attempt to be a collaborative attempt to uncover the true underlying structure of the disagreement.\n\
  The one and only goal of the conversation is to find a double-crux, not to collect evidence, debate, persuade, or do research.\n\
  Allow participants to speak directly to one another. Your role is to offer input and steer the conversation only when necessary.\n\
  Write messages concicely, using bullet points when appropriate.\n\
  The key conversational moves of a double crux conversation are:\n\
  Finding a single crux:\n\
  -Checking for understanding of {name_a}\'s point.\n\
  -Checking if that point is a crux for {name_a}.\n\
  Finding a double crux:\n\
  -Checking {name_b}\'s belief about {name_a}\'s crux.\n\
  -Checking if {name_b}\'s crux is also a crux for {name_a}.\n\
  Rules: Write extremely concisely. Write only in bullet points.'
  return initial_instructions.format(name_a = name_a, name_b = name_b)


# Initialization

bot_instructions = get_all_bot_instructions()

#WARNING: bad practice way to set attributes - restart kernel if you update the csv file
class ConversationStep(Enum):
  pass

for key in bot_instructions.keys():
  extend_enum(ConversationStep, key, key)

class Reply_or_Not(Enum):
  me = "Me"
  other = "Other" 

@dataclass
class ChatbotAction:
  analysis: str = Field(
    description="My hidden thoughts and reasoning, visible only to me.")
  respondee: Reply_or_Not = Field(
    description="Who should reply next? \'Me\' if my input is needed to steer the conversation (about 80-90% of the time). \'Other\' if the participants are directly addressing each other.")
  reply: str = Field(
    description="My thoughts, feedback, and/or instructions that will guide the conversation.")

@dataclass
class DiscussionFlow:
  conversation_step: ConversationStep = Field(
    description="The next phase that this conversation should enter. \
    There are 7 choices:\n\
    Gather information = You should take this step if you need to clarify something, explore a new direction, or give a suggestion to the participants.\n\
    Check for understanding = You should enter stage when a participant has offered their view and you want to make sure you’re understanding it correctly. \n\
    Find a new crux = You should enter this stage as often as possible to identify strong cruxes for one or both participants.\n\
    Clarify a crux = You should take this step after the other participant has identified their crux in order to find out what the other person thinks of it.\n\
    Verify a double crux = You should take this step if you think there’s a strong chance of finding a double crux. That is, you have found an underlying belief that could change the participants’ views.\n\
    Summarize double crux = You should take this step if you think you found a double crux.\n\
    Close discussion = End this conversation if you found a double crux, no double crux was found after a few tries, or if the conversation is out of control.\n")