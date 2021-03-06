
'''
Code directly taken from
Jonathan Shobrook's rebound project:
https://github.com/shobrook/rebound
In accordence with the stated MIT License
https://github.com/shobrook/rebound/blob/master/LICENSE


April 27th 2018 
Edits by Keith Murray
'''
## Helper Functions ##
import random
import requests
from utils import user_agents
import re
import sys
import os
from bs4 import BeautifulSoup


SO_URL = "https://stackoverflow.com"

def stylize_code(soup):
    # NOT IN USE PROBABLY
    """Identifies and stylizes code in a question or answer."""
    # TODO: Handle blockquotes and markdown
    stylized_text = []
    code_blocks = [block.get_text() for block in soup.find_all("code")]
    blockquotes = [block.get_text() for block in soup.find_all("blockquote")]
    newline = False

    for child in soup.recursiveChildGenerator():
        name = getattr(child, "name", None)

        if name is None: # Leaf (terminal) node
            if child in code_blocks:
                if newline: # Code block
                    #if code_blocks.index(child) == len(code_blocks) - 1: # Last code block
                        #child = child[:-1]
                    stylized_text.append(("code", u"\n%s" % str(child)))
                    newline = False
                else: # In-line code
                    stylized_text.append(("code", u"%s" % str(child)))
            else: # Plaintext
                newline = child.endswith('\n')
                stylized_text.append(u"%s" % str(child))

    if type(stylized_text[-2]) == tuple:
        # Remove newline from questions/answers that end with a code block
        if stylized_text[-2][1].endswith('\n'):
            stylized_text[-2] = ("code", stylized_text[-2][1][:-1])

    return urwid.Text(stylized_text)


def get_search_results(soup):
    """Returns a list of dictionaries containing each search result."""
    search_results = []


    for result in soup.find_all("div", class_="question-summary search-result"):
        print(result)
        print('*'*30)
        print(result.find_all("div", class_="result-link"))
        print('*'*30)
        print(result.find_all("div", class_="result-link")[0].find_all('span'))
        title_container = result.find_all("div", class_="result-link")[0].find_all("span")[0].find_all("a")[0]

        if result.find_all("div", class_="status answered") != []: # Has answers
            answer_count = int(result.find_all("div", class_="status answered")[0].find_all("strong")[0].text)
        elif result.find_all("div", class_="status answered-accepted") != []: # Has an accepted answer (closed)
            answer_count = int(result.find_all("div", class_="status answered-accepted")[0].find_all("strong")[0].text)
        else: # No answers
            answer_count = 0

        search_results.append({
            "Title": title_container["title"],
            "Body": result.find_all("div", class_="excerpt")[0].text,
            "Votes": int(result.find_all("span", class_="vote-count-post ")[0].find_all("strong")[0].text),
            "Answers": answer_count,
            "URL": SO_URL + title_container["href"]
        })

    return search_results


def souper(url):
    """Turns a given URL into a BeautifulSoup object."""
    html = requests.get(url, headers={'User-Agent': random.choice(user_agents.USER_AGENTS)})

    if re.search("\.com/nocaptcha", html.url): # URL is a captcha page
        return None
    else:
        return BeautifulSoup(html.text, "html.parser")


## Main ##


def search_stackoverflow(query):
    """Wrapper function for get_search_results."""
    soup = souper(SO_URL + "/search?pagesize=50&q=%s" % query.replace(' ', '+'))

    # TODO: Randomize the user agent

    if soup == None:
        return (None, True)
    else:
        return (get_search_results(soup), False)


def get_question_and_answers(url):
    """Returns details about a given question and list of its answers."""
    soup = souper(url)

    if soup == None: # Captcha page
        return "Sorry, Stack Overflow blocked our request. Try again in a couple seconds.", "", "", ""
    else:
        question_title = soup.find_all('a', class_="question-hyperlink")[0].get_text()
        question_stats = soup.find_all("span", class_="vote-count-post")[0].get_text() # Vote count

        try:
            question_stats = question_stats + " Votes | " + '|'.join((((soup.find_all("div", class_="module question-stats")[0].get_text())
                .replace('\n', ' ')).replace("     ", " | ")).split('|')[:2]) # Vote count, submission date, view count
        except IndexError:
            question_stats = "Could not load statistics."

        question_desc = stylize_code(soup.find_all("div", class_="post-text")[0]) # TODO: Handle duplicates
        question_stats = ' '.join(question_stats.split())

        answers = [stylize_code(answer) for answer in soup.find_all("div", class_="post-text")][1:]
        if len(answers) == 0:
            #answers.append(urwid.Text(("no answers", u"\nNo answers for this question.")))
            answers.append(("no answers", u"\nNo answers for this question."))

        return question_title, question_desc, question_stats, answers

