# Design

## Parts

- IR: An intermediate representation used for communication and containment of command call features.
- Model: A LLM model of some sort. It will be shown a prompt telling it about the scenario, what it is expected to do, and command syntax. 
- Resource: A bound python command and a manual with IR syntax and examples.
- Parser: A parser designed to extract recognized command information into IR format, and convert
  content in IR format back into the local syntax.
- Prompter: A mechanism for prompting a model

## Large parts

- Subagent: A collection of a model, a parsor, and various
- Agent: The main class used to get things done. May contain any
  number of subagents, and those subagents may spawn more subagents.


## IR

### Pytree schema

The PyTree schema is a schema representing
the pytree format I ultimately want to end up
getting features formatted as. Whether the 
root language is xml, json, whatever, I want in the end
to identify what schema we are matching and parse 
into that language.

Each schema is a pytree. You can assume the leafs
of the pytree are one of the following:

- string 
- int
- bool
- float

Sometimes, a string may be explictly specified, as well, as
in the case

schema = {"command" : "keep_alive"}

Meanwhile, the branches can be

- dict
- list

The top level is always a dictionary, which always
has a "command" feature with a name, and is used
to figure out what command we are actually running.

The purpose is to match an issued command to figure out
what command binding we need to run.

## Prompting

Models will start up with relatively sophisticated
prompting which lets the model know what it is and 
what it can do. 

This prompting resource is tied to a parser, whcih
in turn may be tied to resource-specific modules.

## Command bindings and resources

### Objectives

When designing the command and resource interface, there are 
several objectives we need to meet

- Bind the command into something that can be parsed to execute the command
- Tell the model how to execute the command
- Keep things flexible enough the model can engage however it feels most appropriate

### Design

To do this we develop the following architecture

- Somehow, in a file or whatever, one defines a command, a schema, a manual page, and
  some examples to substitute into the manual page.
- The command is converted into an IR representation. This can
  be generated, in theory, from multiple schemas.
- A syntax parser renders the manual page into the
  interaction syntax, then listens for those
  commands.

We will need to bind commands to something
models can use. This discusses how to do it. Commands
are parsed into a manual file and bindings in an
intermediate

## Models

### Objectives

Some objectives to think about while designing how to
use models

- Models should be fairly interchangable
- Models should have control over their resources, and also be shown
  their available resources
- Models should be able to specialize and cross communicate
- Models should be able to think and try other options if something
  initially does not work.

### Design

To accomplish these objectives:

- Models are associated with parsers which are capable of
  displaying hierarchical information in the local format
- Models can view the resource modules available, and can view the models available.
- Models can assign resources to another model and tell them to complete a task, like
  navigate a resource or like remember information.
- Models can decide to code other modules, and can 

## A