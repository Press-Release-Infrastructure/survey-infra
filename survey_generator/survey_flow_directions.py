pg1 = """
We are working on a non-profit project for research purposes to classify business headlines. This is an introductory survey that will take about %s minutes. <b>We will contact "Super workers" who have high rates of accuracy with additional opportunities to work.</b>
<br><br>
The purpose of our project is to identify <b>company acquisitions</b> and <b>mergers</b> from a large number of business headlines. 
<br><br>
An <b>acquisition</b> is when one company buys another company. 
<br><br>
A <b>merger</b> is when two companies join together as equals.
"""

pg1_alt = """
<b>Congratulations!</b> You were identified as a high-accuracy worker and so have the opportunity for additional work completing a follow-up survey on our research project. If you continue to complete surveys with high accuracy, you will receive opportunities to complete additional surveys.
<br><br>
To remind you, we are researchers working on a not for profit project to identify <b>company acquisitions</b> and <b>mergers</b> from a large number of business headlines. 
<br><br>
An <b>acquisition</b> is when one company buys another company. 
<br><br>
A <b>merger</b> is when two companies join together as equals.
"""

pg2 = """
<b>Your role is to read each headline presented and answer three questions:</b>
<br><br>
1. Does the headline describe a company acquisition? <br>
2. Does the headline describe a company merger? <br>
3. What is the <b>name of the company</b> that is the acquirer (the buyer)? <br>
4. What is the <b>name of the company</b> that is acquired (bought)?
"""

pg3 = """
Sometimes, you will <b>not be sure</b> about the answers. 
<br><br>
<ul>
<li>If you are not sure if the headline is an acquisition, you can enter "Neither / Not sure / Unclear."</li>
<li>If the headline does not say, or you are not sure who is the acquirer or acquired company, leave one or both text boxes blank.</li>
<li>For mergers, the companies join as equals. Order does not matter. Enter the <b>name of each company</b> in the text boxes.</li>
</ul>
"""

pg4 = """
Your task is to review a maximum of %s headlines, which will take about %s minutes.
<br><br>
First, we will provide training. We will show you examples of headlines and how they should be classified.
<br><br>
Then, you will start the work of reading headlines and recording acquisitions. 
<br><br>
<b>We will periodically include test headlines at random intervals to check that you are paying attention.</b> If you answer test headlines correctly, you will have the opportunity to do more work on this project. We will contact you with additional survey opportunities. 
"""

pg5 = """
<b>%s</b>
<br><br>
This headline is about an <b>acquisition</b>. We click "Acquisition" in the drop-down box.
<br><br>
In this headline, %s acquires %s. 
<br><br>
We COPY and PASTE the names of the company that was the acquirer (the buyer) and the aquiree (the company purchased).
"""

pg6 = """
<b>%s</b>
<br><br>
This headline is about an acquisition. We click "Acquisition" in the drop-down box.
<br><br>
This headline uses the passive voice: %s was <b>acquired by</b> %s. For this headline, %s is the acquirer and %s the acquiree.
<br><br>
We COPY and PASTE the correct names into the text boxes.
"""

pg7 = """
<b>%s</b>
<br><br>
This headline is about a <b>merger</b>. We click "Merger" in the drop-down box.
<br><br>
The headline says which companies are in the mergers. For mergers, the order does not matter. 
<br><br>
We COPY and PASTE the names into the text boxes, in either order.
"""

pg8 = """
<b>%s</b>
<br><br>
This headline is not about an acquisition or merger. We click "Neither / Not sure / Unclear" in the drop-down box
"""

pg9 = """
<b>%s</b>
<br><br>
This headline is about an <b>acquisition</b>. It talks about a company being "bought," which is another way of saying acquired. We click "Acquisition" in the drop-down box.
<br><br>
This headline writes that %s was the acquirer. But it does not say who the acquired company was. 
<br><br>
We COPY and PASTE %s in the acquirer box, and leave the "acquiree" box blank, and move to the next, clicking the forward arrow.
"""

pg10 = """
<b>%s</b>
<br><br>
This headline is about an <b>acquisition</b>. It talks about a company being "purchased," which is another way of saying acquired. We click "Acquisition" in the drop-down box.
<br><br>
This headline writes that %s was acquired. But it does not say what company was the acquirer.
<br><br>
We COPY and PASTE %s in the acquiree box, and leave the "acquirer" box blank, and move to the next, clicking the forward arrow.
"""

pg11 = """
<b>%s</b>
<br><br>
This text is not a headline. So we click "Neither / Not sure / Unclear" in the drop-down box.
"""

pg12 = """
Training is complete! Remember, your task is to:
<br><br>
<ol>
<li>Decide if you think the headline refers to an acquisition or merger. Some other words used are purchased or bought.</li>
<li>If you think the headline is about an acquisition or merger, enter that in the drop-down box.</li>
<li>If the headline is not about an acquisition or merger, click "Neither / Not sure / Unclear" in the drop-down box.</li>
<li>If you are not sure, click "Neither / Not sure / Unclear." It is better to be conservative. If you are at all unsure, click "Neither / Not sure / Unclear." Don’t spend too long deciding.</li>
<li>For headlines that are an acquisition or merger, the next step is to fill out the text boxes. COPY and PASTE the name of the acquirer company and the acquired company.</li>
<li>If you are not sure the names of the companies, leave one or both text boxes blank.</li>
</ol>
"""

pg13 = """
Some tips before you start:
<br><br>
<ol>
<li>It is faster to use your keyboard (not your mouse) to move to different fields. If you TAB, you will move to the next field. You can select the drop-down box response with the first letter: "A", "M", or "N."</li>
<li>To enter the names of the companies, you will need to use your mouse to highlight the name to COPY and PASTE.</li>
</ol>
"""

pg14 = """
REMEMBER: it is most important to be accurate. DO NOT RUSH. 
<br><br>
<b><i>We will be including "test" headlines in random places to check your work.</i></b>
<br><br>
Once the task is complete, we will assign you a code for you to enter. IT IS IMPORTANT YOU ENTER THE CORRECT CODE. We will use this code to issue payment for the work you have done.
<br><br>
Let’s get started!
"""
