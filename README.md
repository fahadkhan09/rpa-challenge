# RPA Challenge

The process is to automate the extracting of data from the New York times site.

## Process

### Process based on the following steps

- WorkItem data (search phrase, category, month) are the parameters to get the required news.
- The title, date, description, picture filename, count of search phrase and boolean based on amount has to store for
  each news item on the result page.
- Excel has to be generated based on the data stored.

### The technology used in the process:

- Python
- RPAFramework, Selenium

## Robocorp Deployment

- Go to [Robo Corp](https://robocorp.com/)
- Upload the bot (generated with rcc create cmd) to the robot.
- Create a new process, select the bot and define configuration (optional).
- Run the process with input data (WorkItems).
- Add WorkItems as a Json, items should be `search_phrase`, `months` and `sections`


## Local Run
- Install the requirements.txt file by pip
- Run the task.py file
- The news data can be also modified in task.py file 