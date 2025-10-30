/superpowers:brainstorm look through the @backend/src/prompts.py , i want to create a new prompt that takes in the summary of what the user has said and break it into an array of 
"actors", "point_of_conflict", and general details surrounding, so i can have a more well-formed summary of the drama to feed to get the goal generator system more accurate 


guidelines:
- this summary extractor will replace the one that currently is used to get the goal generator system
- it should be as detailed as possible
- the ai agent system prompt should be sifting as finely as possible for any perceived conflict from the summary
- it will now go summary extractor -> structured extraction + goal generator -> then start the questions