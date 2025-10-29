

i want to build an interactive frontend for my agentic drama detector

<features>
- this app is meant for mobile-use primarily and that should be taken into account when writing it. 
- it is written with tailwind css, next and typescript
- this drama detector will have an intake section, for MVP it is just a textbox to input the summary of the drama, but later it will allow you to upload screenshots
- once the drama is uploaded, the application will take you through a series of multiple choice questions that is generated from the backend
- once the app is complete with the goals of the application, it will analyze the drama in a loading state and then put out a analysis of what had occurred
</feautres>


<meat_and_potatoes>
- it should use redux thunks
- it should use shadcn as its design system and utilize the mcp for the best up to date mobile compatible features
</meat_and_potatoes>


<front_page>
the front page will be a page that has two buttons, screenshots or deets
</front_page>

<screenshot_page>
the user will be prompted to upload up to 3 screenshots for the AI to analyze and get the drama from
</screenshot_page>

<deets_page>
the user will be prompted to type out a summary of their drama
</deets_page>

<screenshots>
the following screenshots are from the commandline version of the application, these will serve as guidance but we need to make the app be mobile friendly and follow mobile design guideline as this will be a viral app for gen z to send to their friends. the two images provided are analysis_page.png and question_page.png
</screenshots>

<question_page>
- the question page features a question on the front and then 4 buttons that represent the different questions being asked, and an input field on the bottom that allows the user to enter their own answer if they are not satisfied with the pre generated answers
</question_page>

<analysis_page>
the analysis page will feature a formatted output with an ability to screenshot and share the analysis as a photo and share amongst your friends
</analysis_page>

<guidelines>
- heavily focus on getting 0-1, later improvements, optimizations and superfluous things can be thought about after
- use good proven design patterns like async thunks, selectors, and react-redux stores
- build out a design library of shared components from shadcn to have the most responsive application, we can bring in more figma designs if necesary
</guidelines>


<reference>
use this repo as reference to understand how the frontend will be interacting with the backend, especially the api/investigate and understand those structures to form equivalent frontend structures
</reference>