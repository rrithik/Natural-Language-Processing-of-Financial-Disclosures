# Natural Language Processing of Financial Disclosures

## Project Description
Develop a user friendly application to translate a large set of documents into English and to perform topic analysis on them.

## Team Roster & Contacts
Rithik Reddy – Admin (full access) nibbarar@oregonstate.edu

Norman O’Brien – Collaborator (Read, Write) obrienno@oregonstate.edu 

Hsun-Yu Kuo – Collaborator (Read, Write) kuohsu@oregonstate.edu

Trinity Paulson – Collaborator (Read, Write) paulsotr@oregonstate.edu

Dr. Blackburne – Partner (Read, view-only)

## LICENSE
pending partner confirmation

## Branching flow:
feature/* → PR → ≥ 1 review → merge


#  How to Run the Project

This repository contains the initial **text scraping pipeline** for our *Natural Language Processing of Financial Disclosures* project.  
The scraper reads a local `.txt` file (e.g., SEC 8-K filing) and extracts all text content for topic analysis.

##  Setup & Execution
Clone the repository:

`git clone https://github.com/rrithik/Natural-Language-Processing-of-Financial-Disclosures.git
cd Natural-Language-Processing-of-Financial-Disclosures`

Prepare your input file:

Place your `.txt` document (for example: sample_8K.txt) inside the project folder.
Open the scraper script (e.g., scraper_basic.py) and update the filename variable at the top of the file to match your document name:
file_name = "sample_8K.txt"
### Run the scraper:
`python scraper_basic.py`
### View output:

The program will print the extracted text or save it to an output file (depending on the current configuration).
### **Top 15 Most Common Words in This Filing**

| Word | Frequency | Percentage of Total Words |
|------|------------|----------------------------|
| other | 301 | 1.06% |
| cash | 214 | 0.75% |
| services | 212 | 0.75% |
| december | 208 | 0.73% |
| billion | 200 | 0.70% |
| net | 184 | 0.65% |
| tax | 183 | 0.64% |
| including | 181 | 0.64% |
| sales | 181 | 0.64% |
| income | 171 | 0.60% |
| operating | 165 | 0.58% |
| which | 165 | 0.58% |
| financial | 147 | 0.52% |
| costs | 133 | 0.47% |
| customers | 129 | 0.45% |

---

### **Estimated Topic Distribution**

| Topic | Word Count | Percentage of Total |
|--------|-------------|--------------------|
| Financial Performance | 543 | 1.91% |
| Management / Leadership | 131 | 0.46% |
| Risk / Compliance | 82 | 0.29% |
| Market / Operations | 338 | 1.19% |



