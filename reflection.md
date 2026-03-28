# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**
### Three core actions the user should be able to perform are
1. add a pet
2. a summary showing what should be done that day
3. shedule a service

### Potential Edge Cases
1. What if the owner has no time in that day?
2. More than 5 pets, scheduling complexity

- Briefly describe your initial UML design.
The initial design I kept it simple and follwed the reqs from the README closely. After the initial brainstorm with claude code
there was some clarity issuses for me, just understanding what the main objects would look like and how they connect. And so after some refining I came to understand that there's 4 main objects to the design.

- What classes did you include, and what responsibilities did you assign to each?
The 4 main classes are:
1. Owner
1. Pet
1. Task
1. Scheduler

**b. Design changes**

- Did your design change during implementation?
Yes it changed where at first there we're 6 main objects, the 4 mentioned before and plus 2: DailyPlan and Calendar. After 2/3 iterations it came back down to 4, eliminating the calendar entirely and aggregating DailyPlan and Scheduler.

- If yes, describe at least one change and why you made it.
So DailyPlan isn't independent of Scheduler. It's just the output of the Schedule so it was okay to fold its attributes in Schedle directly to produce a cleaner design. Also the preferences are a bit complex since there's so many scenarios to consider. 


---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
*Answer*: I would add a calendar system to the app so that the user can have a general sense of what's happening during the week. 

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
