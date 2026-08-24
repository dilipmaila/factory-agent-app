========================================================================================
Smart AI Assistant for Factory Operators: Solution Design
========================================================================================

.. contents:: Table of Contents
   :depth: 3
   :local:
   :backlinks: entry

.. note::
   **Companion Documents**:
   
   * Code Guide: `code_and_modules_guide.rst <code_and_modules_guide.rst>`_
   * Run & Setup Guide: `run_and_configuration_guide.rst <run_and_configuration_guide.rst>`_

----------------------------------------------------------------------------------------

1. Summary & Problem
====================

1.1 What is the Problem?
------------------------
In factories, when a machine stops working, operators need help to fix it[cite: 5]. Traditional AI bots fail because they give the exact same answer to everyone[cite: 5]. 
* A new operator gets confused by short, expert-level text[cite: 5]. 
* An expert gets annoyed by long, step-by-step beginner guides[cite: 5]. 
* Also, an expert on Machine A might be a total beginner on Machine B[cite: 5]. The AI needs to know this difference[cite: 5].

1.2 How We Solve It
-------------------
We built a Smart AI Assistant that learns what each operator needs[cite: 5]. 

.. list-table:: Problems & Our Solutions
   :widths: 35 65
   :header-rows: 1

   * - Factory Problem
     - Our Solution
   * - **One answer for everyone**
     - AI changes its answer style (Pictures, Short Text, or Long Text) based on the user[cite: 5].
   * - **Expert on one machine, beginner on another**
     - AI separates "Reading Style" from "Machine Skill"[cite: 5]. It knows what you are good at[cite: 5].
   * - **Manuals never update with field tricks**
     - AI learns new tricks from workers but hides them until 3 Experts approve them[cite: 5].
   * - **Temporary fixes (The Duct-Tape problem)**
     - AI waits 8 hours to see if a fix is permanent before rewarding itself[cite: 5].
   * - **Workers get tired at the end of a shift**
     - AI tracks shift hours[cite: 5]. If a worker is tired, it only gives short, direct answers[cite: 5].

1.3 Basic Rules (Assumptions)
-----------------------------
To make this work in real life, we assume:
1. **Unique Logins**: Every worker has their own ID[cite: 5]. 
2. **Sensor Connection**: The AI can read live machine data (SCADA) to see if a machine is fixed[cite: 5].
3. **Read-Only AI**: The AI only gives advice[cite: 5]. It cannot control the machine directly[cite: 5].
4. **Fixing the Machine = Good AI**: If the machine works again quickly and stays working, the AI did a good job[cite: 5].

----------------------------------------------------------------------------------------

2. How the System Works (The Flow)
==================================

The system has two main parts so it does not slow down during work hours[cite: 5]:
1. **The Fast Loop (Real-Time)**: Works instantly while the operator chats[cite: 5]. It only reads data and saves logs quickly so the screen never freezes[cite: 5].
2. **The Overnight Loop (Sleep Cycle)**: Runs at 3:00 AM[cite: 5]. It does the heavy thinking, updates user profiles, and learns new tricks while no one is working[cite: 5].

2.1 Simple Flowchart
--------------------
.. code-block:: text

   OPERATOR CHATS WITH AI -> AI CHECKS HOW TIRED THEY ARE -> AI CHECKS THEIR SKILL LEVEL
         |
         v
   AI FINDS THE MANUAL -> AI CHOOSES THE BEST REPLY FORMAT -> AI SENDS THE ANSWER
         |
         v
   MACHINE IS FIXED -> AI SAVES A QUICK LOG -> (AT 3:00 AM) AI UPDATES SKILLS & LEARNS

----------------------------------------------------------------------------------------

3. The Core Parts of the System
===============================

3.1 Six Types of Memory
-----------------------
The AI stores information in six different ways to stay smart and fast[cite: 5]:

1. **Short-Term Memory**: Holds the current chat, live sensor data, and safety warnings just for this one session[cite: 5].
2. **Operator Profiles (Knowledge Graph)**: Remembers how good an operator is at a specific machine, and how they like to read (Pictures vs. Text)[cite: 5].
3. **Dynamic Troubleshooting Trees**: Ranks repair steps by success rate[cite: 5]. If Step 1 works 90% of the time, the AI suggests it first[cite: 5].
4. **Sandbox (Quarantine)**: A safe place to store new repair tricks discovered by workers[cite: 5]. 
5. **History Log**: A fast list of everything that happened today (successes and failures)[cite: 5].
6. **Official Manuals**: The original factory documents (PDFs/Text) used for searching[cite: 5].

3.2 Smart Operator Profiles
---------------------------
To fix the problem of an expert switching to a new machine, we separate two things[cite: 5]:
* **Machine Skill**: John is an "Expert" on the CNC Machine, but a "Novice" on the Molding Machine[cite: 5].
* **Reading Style**: When John is a "Novice", he prefers Pictures[cite: 5]. When John is an "Expert", he prefers Short Text[cite: 5]. 
* **Training Updates**: If John passes a training course in the HR system, the AI instantly updates him to "Expert" overnight[cite: 5].

3.3 Choosing the Reply Format (Smart Selector)
----------------------------------------------
The AI uses a smart scoring system to pick how it replies[cite: 5]:
* **Visual**: Step-by-step pictures and safety tags[cite: 5]. Good for beginners[cite: 5].
* **Terse (Short)**: Just 2-3 bullet points of pure data[cite: 5]. Good for experts[cite: 5].
* **Detailed**: Long explanations of why something broke[cite: 5]. 

**The Fatigue Rule**: If the worker has been on shift for 10 hours, they are tired[cite: 5]. The AI stops testing new formats and only gives short, direct answers to save their energy[cite: 5].

**Manual Override**: If the AI gives pictures but the worker clicks a "Give me Text" button, the AI changes immediately[cite: 5]. It also heavily punishes its own scoring system so it remembers for next time[cite: 5].

3.4 Finding the Right Manual
----------------------------
When a worker searches for an error like "Alarm 102", the AI uses a hyrbid search[cite: 5]. It matches exact words (like "102") AND meaning (like "low pressure") to find the perfect document[cite: 5].

3.5 The 8-Hour Wait Rule (Preventing Temporary Fixes)
-----------------------------------------------------
If an operator fixes a machine fast by doing something unsafe (like using duct tape), the machine will probably break again soon[cite: 5]. 
* **The Rule**: When a machine is fixed, the AI does not reward itself immediately[cite: 5]. It waits 8 hours[cite: 5].
* **Good Fix**: If the machine stays working for 8 hours, the AI gives a positive reward[cite: 5].
* **Bad Fix**: If the machine breaks again within 8 hours, the AI gives a huge negative penalty[cite: 5]. It learns that the fix was bad[cite: 5].

3.6 Learning New Tricks (Quick Follow-Up & 3-Expert Rule)
---------------------------------------------------------
Sometimes workers find a faster way to fix a machine[cite: 5]. 
* **Quick Follow-Up**: If a worker fixes a 15-minute problem in 2 minutes, the AI notices[cite: 5]. The next time they log in, it asks: *"Did you use the valve shortcut? Yes or No?"*[cite: 5].
* **3-Expert Rule (Sandbox)**: If they say Yes, the AI puts this trick in the Sandbox (Quarantine)[cite: 5]. It will NOT show this trick to beginners[cite: 5]. Only when 3 different Experts use the trick successfully will the AI add it to the main manual (and it remains marked for "Experts Only")[cite: 5].

----------------------------------------------------------------------------------------

4. Safety Rules & Problem Prevention
====================================

We built safety rules to prevent the AI from making mistakes[cite: 5].

.. list-table:: Risks & Safety Rules
   :widths: 35 65
   :header-rows: 1

   * - Risk
     - Safety Rule
   * - **Worker does an unsafe temporary fix**
     - AI waits 8 hours to see if it breaks again before learning[cite: 5].
   * - **AI shares a dangerous shortcut**
     - Shortcuts are locked in the Sandbox until 3 Experts approve them[cite: 5].
   * - **Worker gets annoyed by AI format**
     - Worker can click a button to change format instantly[cite: 5].
   * - **AI promotes a beginner too fast**
     - It takes many successes to level up, but only one failure to level down[cite: 5].
   * - **Worker keeps failing at the same problem**
     - AI remembers past failures. It will suggest calling a manager early[cite: 5].
   * - **Worker is too tired to read long text**
     - AI checks shift hours. If tired, it forces short, simple answers[cite: 5].

----------------------------------------------------------------------------------------

5. Testing Plan (Pilot Phase)
=============================

To prove this works in a real factory, we will test it[cite: 5].

5.1 Goals
---------
* Fix machines 25% faster compared to using static PDF manuals[cite: 5].
* The AI should figure out a worker's favorite reading style within 5 to 8 chats[cite: 5].
* The AI must have 0% safety mistakes[cite: 5].

5.2 How We Measure Success
--------------------------
1. **Time to Repair**: How fast the machine sensors show it is working again[cite: 5].
2. **Success Rate**: How often workers fix it without calling a manager[cite: 5].
3. **Temporary Fix Rate**: How many machines break again within 8 hours (Goal: less than 5%)[cite: 5].

----------------------------------------------------------------------------------------

6. Real-Life Examples
=====================

**Example 1: A Beginner on a CNC Machine**
John is a Beginner[cite: 5]. He gets an "Alarm 102"[cite: 5]. The AI knows his skill level[cite: 5]. It gives him a visual, step-by-step guide with big safety warnings[cite: 5]. He fixes it[cite: 5]. The AI waits 8 hours, sees the machine is still working, and gives John a small skill upgrade[cite: 5].

**Example 2: An Expert on the Night Shift**
Mike is an Expert, but it is hour 11 of a 12-hour night shift[cite: 5]. The AI knows he is very tired[cite: 5]. Even if it wants to try a new format, it stops itself[cite: 5]. It gives Mike just 2 bullet points of raw data to save his energy[cite: 5]. Because his manager is not at the factory at night, the AI reminds Mike to be extra safe[cite: 5].

**Example 3: Finding a Shortcut**
Sarah is an Expert[cite: 5]. She fixes a machine in 2 minutes instead of 10[cite: 5]. The next day, the AI asks her if she used a shortcut[cite: 5]. She clicks "Yes." The AI saves this shortcut secretly[cite: 5]. Two weeks later, two other Experts do the same thing[cite: 5]. Now, the AI will officially suggest this shortcut to other Experts to save time[cite: 5].