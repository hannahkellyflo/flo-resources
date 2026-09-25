export const PROMPTS = [
 {
  "n": 1,
  "slug": "assess-overall-pipeline-health",
  "title": "Assess overall pipeline health",
  "prompt": "How's our lateral partner pipeline? Help me explore different data to assess its health.",
  "category": "Lateral and partner hiring",
  "theme": "Where the pipeline stands",
  "jobs": [
   "Check where things stand"
  ],
  "vars": []
 },
 {
  "n": 2,
  "slug": "pull-a-status-list",
  "title": "Pull a status list",
  "prompt": "Who are all of my candidates in [Status] for [Position Type]?",
  "category": "Lateral and partner hiring",
  "theme": "Where the pipeline stands",
  "jobs": [
   "Find people or records"
  ],
  "vars": [
   "[Status]",
   "[Position Type]"
  ],
  "req": "Pro tip: Ensure the [Position Type] field is filled in for your jobs / searches."
 },
 {
  "n": 4,
  "slug": "audit-which-statuses-you-actually-use",
  "title": "Audit which statuses you actually use",
  "prompt": "Which statuses aren't being used that we should consider removing?",
  "category": "Lateral and partner hiring",
  "theme": "Where the pipeline stands",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 5,
  "slug": "brief-your-managing-partner-on-the-pipeline",
  "title": "Brief your managing partner on the pipeline",
  "prompt": "Give me a concise summary of each candidate in the [Job] pipeline who has progressed to the interview stage, formatted so I can share it with hiring stakeholders.",
  "category": "Lateral and partner hiring",
  "theme": "Where the pipeline stands",
  "jobs": [
   "Draft something"
  ],
  "vars": [
   "[Job]"
  ]
 },
 {
  "n": 6,
  "slug": "break-the-pipeline-down-by-your-custom-fields",
  "title": "Break the pipeline down by your custom fields",
  "prompt": "Break down my lateral partner pipeline by client portability assessment, conflicts status, and LPQ status.",
  "category": "Lateral and partner hiring",
  "theme": "Where the pipeline stands",
  "jobs": [
   "Check where things stand"
  ],
  "vars": [],
  "req": "Requires use of [Conflict Status], [Portability Assessment], [LPQ Status], or related custom fields in your system."
 },
 {
  "n": 7,
  "slug": "find-the-conflicts-checks-that-are-holding-you-up",
  "title": "Find the conflicts checks that are holding you up",
  "prompt": "Give me the list of partners farthest along in our hiring process who haven't started the conflicts process, and include their agency contact.",
  "category": "Lateral and partner hiring",
  "theme": "Where the pipeline stands",
  "jobs": [
   "Chase or follow up"
  ],
  "vars": []
 },
 {
  "n": 8,
  "slug": "spot-cross-posting-overlaps",
  "title": "Spot cross-posting overlaps",
  "prompt": "Show me law students who applied to more than one office or class year, and where the overlaps are across our applications.",
  "category": "Lateral and partner hiring",
  "theme": "Where the pipeline stands",
  "jobs": [
   "Find people or records"
  ],
  "vars": []
 },
 {
  "n": 10,
  "slug": "find-candidates-by-degree-or-background",
  "title": "Find candidates by degree or background",
  "prompt": "Show me every candidate in the pipeline for [Job] who has a technical or science degree.",
  "category": "Lateral and partner hiring",
  "theme": "Look up a candidate",
  "jobs": [
   "Find people or records"
  ],
  "vars": [
   "[Job]"
  ]
 },
 {
  "n": 11,
  "slug": "filter-on-application-question-answers",
  "title": "Filter on application question answers",
  "prompt": "Show me all candidates who selected [Office] as their office location interest.",
  "category": "Candidate sourcing",
  "theme": "Interest and follow-up lists",
  "jobs": [
   "Find people or records"
  ],
  "vars": [
   "[Office]"
  ],
  "req": "Requires use of [Office] as an Application Question, Qualifying Question, or Internal Field in your system."
 },
 {
  "n": 12,
  "slug": "find-candidates-with-real-ties-to-a-market",
  "title": "Find candidates with real ties to a market",
  "prompt": "Which candidates in our pipeline have a personal or professional connection to [Market]?",
  "category": "Lateral and partner hiring",
  "theme": "Look up a candidate",
  "jobs": [
   "Find people or records"
  ],
  "vars": [
   "[Market]"
  ]
 },
 {
  "n": 13,
  "slug": "check-whether-you-ve-seen-someone-before",
  "title": "Check whether you've seen someone before",
  "prompt": "Have we received [Candidate Name] before? Summarize any prior applications, feedback, and statuses including dates.",
  "category": "Lateral and partner hiring",
  "theme": "Look up a candidate",
  "jobs": [
   "Find people or records"
  ],
  "vars": [
   "[Candidate Name]"
  ]
 },
 {
  "n": 14,
  "slug": "reconstruct-your-history-with-a-candidate",
  "title": "Reconstruct your history with a candidate",
  "prompt": "When did we last meet with [Candidate Name], who from the firm met with them, and what did they say?",
  "category": "Lateral and partner hiring",
  "theme": "Look up a candidate",
  "jobs": [
   "Find people or records"
  ],
  "vars": [
   "[Candidate Name]"
  ]
 },
 {
  "n": 16,
  "slug": "summarize-years-of-relationship-notes",
  "title": "Summarize years of relationship notes",
  "prompt": "Summarize everything we know about [Candidate Name]. Pull together the notes and communications from the years we've been building this relationship.",
  "category": "Lateral and partner hiring",
  "theme": "Look up a candidate",
  "jobs": [
   "Find people or records"
  ],
  "vars": [
   "[Candidate Name]"
  ]
 },
 {
  "n": 17,
  "slug": "rank-your-agencies-by-who-you-actually-hire",
  "title": "Rank your agencies by who you actually hire",
  "prompt": "Rank the agencies in my database by how many candidates they've submitted who we've hired.",
  "category": "Lateral and partner hiring",
  "theme": "Agencies and search firms",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 18,
  "slug": "compare-submission-volume-against-quality",
  "title": "Compare submission volume against quality",
  "prompt": "Which agencies submit a high volume of candidates, but a low ratio of candidates who make it to offer?",
  "category": "Lateral and partner hiring",
  "theme": "Agencies and search firms",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 19,
  "slug": "define-best-agency-by-outcome-quality",
  "title": "Define 'best agency' by outcome quality",
  "prompt": "Who are my best agency partners by outcome quality, meaning the share of candidates they submitted who reached offer extended, accepted, or declined?",
  "category": "Lateral and partner hiring",
  "theme": "Agencies and search firms",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 20,
  "slug": "compare-agency-speed",
  "title": "Compare agency speed",
  "prompt": "Is time to offer any faster for candidates working with certain agencies? Show me average time to offer by agency.",
  "category": "Lateral and partner hiring",
  "theme": "Agencies and search firms",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 21,
  "slug": "trace-one-agency-s-submissions",
  "title": "Trace one agency's submissions",
  "prompt": "List every candidate submitted by [Agency] for [Job] and show me whether we interviewed them.",
  "category": "Lateral and partner hiring",
  "theme": "Agencies and search firms",
  "jobs": [
   "Find people or records"
  ],
  "vars": [
   "[Agency]",
   "[Job]"
  ]
 },
 {
  "n": 22,
  "slug": "catch-duplicate-agency-submissions",
  "title": "Catch duplicate agency submissions",
  "prompt": "Show me candidates who have been submitted by more than one search firm, and which submission came first.",
  "category": "Lateral and partner hiring",
  "theme": "Agencies and search firms",
  "jobs": [
   "Find people or records"
  ],
  "vars": []
 },
 {
  "n": 23,
  "slug": "find-where-your-process-slows-down",
  "title": "Find where your process slows down",
  "prompt": "What is our average time to hire on [Job], and where do we slow down the most in the process?",
  "category": "Lateral and partner hiring",
  "theme": "Speed, timing, and trends",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[Job]"
  ]
 },
 {
  "n": 24,
  "slug": "ask-for-a-chart",
  "title": "Ask for a chart",
  "prompt": "Give me the average time to hire for my [Department] positions, then break it down by office location and practice area.",
  "category": "Lateral and partner hiring",
  "theme": "Speed, timing, and trends",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[Department]"
  ],
  "req": "Pro tip: Keep your [Department] options up to date in Organization Settings."
 },
 {
  "n": 25,
  "slug": "segment-velocity-by-specialty",
  "title": "Segment velocity by specialty",
  "prompt": "What is the average time to offer for our [Practice Area] candidates?",
  "category": "Lateral and partner hiring",
  "theme": "Speed, timing, and trends",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[Practice Area]"
  ],
  "req": "Requires use of [Practice Area] as an Application Question, Qualifying Question, or Internal Field in your system."
 },
 {
  "n": 27,
  "slug": "pull-student-offer-yield-by-school-and-source",
  "title": "Pull student offer yield by school and source",
  "prompt": "What is our offer yield, accept rate, and decline rate for [Season], broken down by law school and by source?",
  "category": "Candidate sourcing",
  "theme": "What events and schools produce",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[Season]"
  ]
 },
 {
  "n": 28,
  "slug": "stay-on-top-of-firm-wide-law-student-recruiting",
  "title": "Stay on top of firm-wide law student recruiting",
  "prompt": "How many law student callbacks have we completed and how many offers are still outstanding? Break it down by office.",
  "category": "Candidate sourcing",
  "theme": "Interview logistics",
  "jobs": [
   "Check where things stand"
  ],
  "vars": []
 },
 {
  "n": 29,
  "slug": "track-monthly-interview-cadence",
  "title": "Track monthly interview cadence",
  "prompt": "How many [Hiring Type] candidates have we had an initial interview with each month this year, and how does that cadence compare year over year?",
  "category": "Lateral and partner hiring",
  "theme": "Speed, timing, and trends",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[Hiring Type]"
  ],
  "req": "Pro tip: Ensure the [Position Type] field is filled in for your jobs / searches."
 },
 {
  "n": 30,
  "slug": "compare-a-full-season-year-over-year",
  "title": "Compare a full season year over year",
  "prompt": "Compare our recruiting results year over year: applications, interviews, offers, and acceptances.",
  "category": "Lateral and partner hiring",
  "theme": "Speed, timing, and trends",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 31,
  "slug": "track-the-evolution-of-your-law-student-recruitment",
  "title": "Track the evolution of your law student recruitment",
  "prompt": "Show me how our law student recruiting has shifted over the past few years: job open dates, application source, interview timing, and offer and acceptance rates.",
  "category": "Lateral and partner hiring",
  "theme": "Speed, timing, and trends",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 32,
  "slug": "run-a-friction-analysis-on-one-team",
  "title": "Run a friction analysis on one team",
  "prompt": "Where are candidates slowing down in the [Job] process? Show me the time between each stage, and where feedback, scheduling or handoffs are holding things up.",
  "category": "Lateral and partner hiring",
  "theme": "Speed, timing, and trends",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[Job]"
  ]
 },
 {
  "n": 33,
  "slug": "get-a-health-check-on-one-job-or-search",
  "title": "Get a health check on one job or search",
  "prompt": "What's happening with the [Job] opening right now? Show me a pipeline overview and what deserves attention first.",
  "category": "Lateral and partner hiring",
  "theme": "Speed, timing, and trends",
  "jobs": [
   "Check where things stand"
  ],
  "vars": [
   "[Job]"
  ]
 },
 {
  "n": 34,
  "slug": "rank-interviewers-by-volume",
  "title": "Rank interviewers by volume",
  "prompt": "Which interviewers have done the most interviews this year? Give me names and counts.",
  "category": "Lateral and partner hiring",
  "theme": "Interviewing and feedback",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 35,
  "slug": "find-your-toughest-and-most-generous-graders",
  "title": "Find your toughest and most generous graders",
  "prompt": "Rank our interviewers from most generous to toughest grader based on the scores they give in candidate evaluations.",
  "category": "Lateral and partner hiring",
  "theme": "Interviewing and feedback",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 36,
  "slug": "read-the-language-behind-the-scores",
  "title": "Read the language behind the scores",
  "prompt": "Give me direct quote examples from the evaluations written by our highest-rating and lowest-rating interviewers.",
  "category": "Lateral and partner hiring",
  "theme": "Interviewing and feedback",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 37,
  "slug": "find-the-right-panel-for-a-key-candidate",
  "title": "Find the right panel for a key candidate",
  "prompt": "Who are my top interviewers for [Practice Group] candidates in the [Office] office, based on who meets candidates who go on to accept offers?",
  "category": "Lateral and partner hiring",
  "theme": "Interviewing and feedback",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[Practice Group]",
   "[Office]"
  ],
  "req": "Requires use of [Practice Area / Office] as an Application Question, Qualifying Question, or Internal Field in your system."
 },
 {
  "n": 39,
  "slug": "connect-interviewers-to-offer-acceptance",
  "title": "Connect interviewers to offer acceptance",
  "prompt": "Which interviewers correlate with the highest candidate offer-acceptance rate, and which correlate with the most declines?",
  "category": "Lateral and partner hiring",
  "theme": "Interviewing and feedback",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 40,
  "slug": "check-one-interviewer-s-track-record",
  "title": "Check one interviewer's track record",
  "prompt": "For [Interviewer], show me every candidate they interviewed this cycle and what percentage of those candidates accepted or declined their offer.",
  "category": "Lateral and partner hiring",
  "theme": "Interviewing and feedback",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[Interviewer]"
  ]
 },
 {
  "n": 41,
  "slug": "find-who-owes-you-feedback",
  "title": "Find who owes you feedback",
  "prompt": "Which candidates have no submitted interview feedback yet? Provide their interviewers.",
  "category": "Lateral and partner hiring",
  "theme": "Interviewing and feedback",
  "jobs": [
   "Chase or follow up"
  ],
  "vars": []
 },
 {
  "n": 42,
  "slug": "draft-the-feedback-chase-up",
  "title": "Draft the feedback chase-up",
  "prompt": "Draft an email to each interviewer listing the candidates from their interviews with no submitted evaluation, Include the link to submit it.",
  "category": "Lateral and partner hiring",
  "theme": "Interviewing and feedback",
  "jobs": [
   "Chase or follow up",
   "Draft something"
  ],
  "vars": []
 },
 {
  "n": 43,
  "slug": "summarize-what-everyone-said-about-a-candidate",
  "title": "Summarize what everyone said about a candidate",
  "prompt": "Give me a summary of what all of our interviewers said about [Candidate Name].",
  "category": "Lateral and partner hiring",
  "theme": "Interviewing and feedback",
  "jobs": [
   "Find people or records"
  ],
  "vars": [
   "[Candidate Name]"
  ]
 },
 {
  "n": 44,
  "slug": "mine-your-free-text-evaluation-questions",
  "title": "Mine your free-text evaluation questions",
  "prompt": "What are the themes in interview evaluations for [Job]? Include supporting quotes from free-text comments.",
  "category": "Lateral and partner hiring",
  "theme": "Interviewing and feedback",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[Job]"
  ]
 },
 {
  "n": 45,
  "slug": "draft-a-candidate-executive-summary",
  "title": "Draft a candidate executive summary",
  "prompt": "Help me draft an executive summary of [Candidate Name]'s candidate profile.",
  "category": "Lateral and partner hiring",
  "theme": "Write it up",
  "jobs": [
   "Draft something"
  ],
  "vars": [
   "[Candidate Name]"
  ]
 },
 {
  "n": 46,
  "slug": "write-the-partnership-vote-memo",
  "title": "Write the partnership vote memo",
  "prompt": "Prepare an executive summary of [Candidate Name] for the partnership to review ahead of their voting session.",
  "category": "Lateral and partner hiring",
  "theme": "Write it up",
  "jobs": [
   "Draft something"
  ],
  "vars": [
   "[Candidate Name]"
  ]
 },
 {
  "n": 47,
  "slug": "send-the-internal-offer-update",
  "title": "Send the internal offer update",
  "prompt": "Write an internal email to the Hiring Partner about [Candidate Name]'s offer: current status, why we moved to offer, and next steps.",
  "category": "Lateral and partner hiring",
  "theme": "Write it up",
  "jobs": [
   "Draft something"
  ],
  "vars": [
   "[Candidate Name]"
  ]
 },
 {
  "n": 48,
  "slug": "summarize-a-whole-group-of-candidates-at-once",
  "title": "Summarize a whole group of candidates at once",
  "prompt": "Summarize the candidate profiles of everyone in [Status] for the [Office] office, including most recent role and source.",
  "category": "Lateral and partner hiring",
  "theme": "Write it up",
  "jobs": [
   "Draft something"
  ],
  "vars": [
   "[Status]",
   "[Office]"
  ]
 },
 {
  "n": 49,
  "slug": "update-your-referral-sources",
  "title": "Update your referral sources",
  "prompt": "Write an email summary of all active, referral-sourced candidates, so I can update the people who referred them.",
  "category": "Lateral and partner hiring",
  "theme": "Write it up",
  "jobs": [
   "Draft something"
  ],
  "vars": []
 },
 {
  "n": 50,
  "slug": "mobilize-the-right-people-to-close-an-offer",
  "title": "Mobilize the right people to close an offer",
  "prompt": "Who met [Candidate Name] most often and gave the highest feedback? Draft a note asking each of them to reach out to them during the offer phase.",
  "category": "Lateral and partner hiring",
  "theme": "Write it up",
  "jobs": [
   "Find people or records",
   "Draft something"
  ],
  "vars": [
   "[Candidate Name]"
  ]
 },
 {
  "n": 51,
  "slug": "prep-the-co-chairs",
  "title": "Prep the co-chairs",
  "prompt": "Summarize all of the interview evaluation feedback for [Candidate] and summarize their resume for the hiring committee.",
  "category": "Lateral and partner hiring",
  "theme": "Write it up",
  "jobs": [
   "Draft something"
  ],
  "vars": [
   "[Candidate]"
  ]
 },
 {
  "n": 53,
  "slug": "build-criteria-from-your-own-successful-hires",
  "title": "Build criteria from your own successful hires",
  "prompt": "Look at our successful hires for [Role] and build 5 to 8 criteria we could use to screen new applicants. Use only observable, role-relevant evidence from their applications and work history. For each, give a short label, what to look for, and why it shows up in this group. Avoid generic criteria like “strong background,” and avoid anything that could directly or indirectly stand in for a protected characteristic.",
  "category": "Lateral and partner hiring",
  "theme": "Screening criteria",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[Role]"
  ]
 },
 {
  "n": 54,
  "slug": "reuse-what-you-liked-about-past-candidates",
  "title": "Reuse what you liked about past candidates",
  "prompt": "I'm opening a new position, and I've hired for a similar position [Position Name] in the past. Look at candidates we interviewed. What about them did we like that we should use as qualifications for this role?",
  "category": "Lateral and partner hiring",
  "theme": "Screening criteria",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[Position Name]"
  ]
 },
 {
  "n": 55,
  "slug": "re-engage-the-ones-who-got-away",
  "title": "Re-engage the ones who got away",
  "prompt": "Which summer associate candidates who declined our offer over the last few years and were interested in [Practice Group]? Pull a list with email addresses, GPA, law school, and decline date, then draft an email re-engaging them about our new [Role].",
  "category": "Candidate sourcing",
  "theme": "Student screening",
  "jobs": [
   "Find people or records",
   "Draft something"
  ],
  "vars": [
   "[Practice Group]",
   "[Role]"
  ]
 },
 {
  "n": 56,
  "slug": "look-for-the-pre-law-school-signal",
  "title": "Look for the pre-law-school signal",
  "prompt": "Which summer associate candidates have work experience prior to law school? Pull candidates who worked in law-adjacent industries like consulting or banking. Also look for roles that likely required people skills and intensity, like wait staff at a busy restaurant.",
  "category": "Candidate sourcing",
  "theme": "Student screening",
  "jobs": [
   "Find people or records"
  ],
  "vars": []
 },
 {
  "n": 57,
  "slug": "normalize-grades-across-schools",
  "title": "Normalize grades across schools",
  "prompt": "When you see grades from [Law School], convert each letter grade to this numeric value: [Conversion Table]. Then rank all candidates from that school.",
  "category": "Candidate sourcing",
  "theme": "Student screening",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[Law School]",
   "[Conversion Table]"
  ],
  "req": "Requires use of [GPA] or similar custom field as an Application Question, Qualifying Question, or Internal Field in your system."
 },
 {
  "n": 59,
  "slug": "send-the-weekly-recruiting-update",
  "title": "Send the weekly recruiting update",
  "prompt": "Give me a weekly recruiting update for [Practice Group]. Include candidates who completed interviews and who is scheduled next week, how the application pipeline changed since last month, new leads added per job, roles where projected hires fall short of openings, themes from candidates who turned us down and from those we rejected, anyone at the onsite stage already rated 3 or 4, and where we have moved faster or slower than previous months. Bullet points.",
  "category": "Lateral and partner hiring",
  "theme": "Recurring reporting",
  "jobs": [
   "Check where things stand",
   "Draft something"
  ],
  "vars": [
   "[Practice Group]"
  ]
 },
 {
  "n": 60,
  "slug": "fill-out-an-industry-survey",
  "title": "Fill out an industry survey",
  "prompt": "I need to complete the [NALP] survey pasted below. What answers are readily available in our existing data? What is missing?",
  "category": "Lateral and partner hiring",
  "theme": "Recurring reporting",
  "jobs": [
   "Check where things stand"
  ],
  "vars": [
   "[NALP]"
  ]
 },
 {
  "n": 61,
  "slug": "balance-the-interview-load",
  "title": "Balance the interview load",
  "prompt": "Which attorneys are carrying the most interview load this season, and who could we ask to take on more?",
  "category": "Lateral and partner hiring",
  "theme": "Recurring reporting",
  "jobs": [
   "Check where things stand"
  ],
  "vars": []
 },
 {
  "n": 62,
  "slug": "pull-an-event-registration-list",
  "title": "Pull an event registration list",
  "prompt": "Show me everyone registered for [Event] with their name, school, and email.",
  "category": "Candidate sourcing",
  "theme": "Run an event",
  "jobs": [
   "Find people or records"
  ],
  "vars": [
   "[Event]"
  ]
 },
 {
  "n": 63,
  "slug": "compare-rsvps-to-actual-attendance",
  "title": "Compare RSVPs to actual attendance",
  "prompt": "For [Event], what was our overall attendance rate? Who RSVP'd but did not check in?",
  "category": "Candidate sourcing",
  "theme": "Run an event",
  "jobs": [
   "Check where things stand"
  ],
  "vars": [
   "[Event]"
  ]
 },
 {
  "n": 64,
  "slug": "find-everyone-you-met-on-campus-this-season",
  "title": "Find everyone you met on campus this season",
  "prompt": "Show me every candidate we met at an on-campus event this recruiting season, including the event name.",
  "category": "Candidate sourcing",
  "theme": "Who you met",
  "jobs": [
   "Find people or records"
  ],
  "vars": []
 },
 {
  "n": 65,
  "slug": "trace-where-your-interest-form-traffic-comes-from",
  "title": "Trace where your interest form traffic comes from",
  "prompt": "Break down the candidates who filled out our stay-connected form by [Qualifying Question].",
  "category": "Candidate sourcing",
  "theme": "Run an event",
  "jobs": [
   "Check where things stand"
  ],
  "vars": [
   "[Qualifying Question]"
  ]
 },
 {
  "n": 66,
  "slug": "surface-the-standouts-your-attorneys-flagged",
  "title": "Surface the standouts your attorneys flagged",
  "prompt": "Which candidates did our attorneys flag as standouts at [Event] in their feedback forms?",
  "category": "Candidate sourcing",
  "theme": "Who you met",
  "jobs": [
   "Find people or records"
  ],
  "vars": [
   "[Event]"
  ]
 },
 {
  "n": 67,
  "slug": "summarize-attorney-impressions-of-one-candidate",
  "title": "Summarize attorney impressions of one candidate",
  "prompt": "Summarize the attorney feedback we collected on [Candidate] across all of our events.",
  "category": "Candidate sourcing",
  "theme": "Who you met",
  "jobs": [
   "Find people or records"
  ],
  "vars": [
   "[Candidate]"
  ]
 },
 {
  "n": 68,
  "slug": "draft-the-event-email",
  "title": "Draft the event email",
  "prompt": "Draft an email to everyone registered for [Event] with the event details and our [transportation voucher] link.",
  "category": "Candidate sourcing",
  "theme": "Who you met",
  "jobs": [
   "Find people or records"
  ],
  "vars": [
   "[Event]",
   "[transportation voucher]"
  ]
 },
 {
  "n": 69,
  "slug": "see-everyone-you-ve-met-from-one-school",
  "title": "See everyone you've met from one school",
  "prompt": "Show me the candidates we've met from [Law School] across all of our events this recruiting season.",
  "category": "Candidate sourcing",
  "theme": "Who you met",
  "jobs": [
   "Find people or records"
  ],
  "vars": [
   "[Law School]"
  ]
 },
 {
  "n": 70,
  "slug": "judge-which-events-are-worth-it",
  "title": "Judge which events are worth it",
  "prompt": "Which recruiting events actually lead to hires? Show me conversion rates by law school and by event.",
  "category": "Candidate sourcing",
  "theme": "What events and schools produce",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 71,
  "slug": "identify-your-real-pipeline-schools",
  "title": "Identify your real pipeline schools",
  "prompt": "Which law schools are our strongest pipeline schools based on volume of interviews and offers?",
  "category": "Candidate sourcing",
  "theme": "What events and schools produce",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 72,
  "slug": "build-a-targeted-invite-list",
  "title": "Build a targeted invite list",
  "prompt": "Pull the list of candidates from [Law School] who attended [Event] so I can send them a bulk invitation to apply to [Job].",
  "category": "Candidate sourcing",
  "theme": "Interest and follow-up lists",
  "jobs": [
   "Find people or records"
  ],
  "vars": [
   "[Law School]",
   "[Event]",
   "[Job]"
  ]
 },
 {
  "n": 73,
  "slug": "see-your-whole-event-calendar",
  "title": "See your whole event calendar",
  "prompt": "Show me all of our upcoming law school events in one place: school, date, attending attorneys, and registration counts.",
  "category": "Candidate sourcing",
  "theme": "Interest and follow-up lists",
  "jobs": [
   "Check where things stand"
  ],
  "vars": []
 },
 {
  "n": 74,
  "slug": "track-qr-code-signups",
  "title": "Track QR code signups",
  "prompt": "How many candidates have registered through our stay-connected form \"event\" this season, and at which schools?",
  "category": "Candidate sourcing",
  "theme": "Interest and follow-up lists",
  "jobs": [
   "Check where things stand"
  ],
  "vars": []
 },
 {
  "n": 79,
  "slug": "find-when-an-interviewer-is-usually-free",
  "title": "Find when an interviewer is usually free",
  "prompt": "When is [Interviewer] usually free to interview based on their past interview schedules?",
  "category": "Candidate sourcing",
  "theme": "Interview logistics",
  "jobs": [
   "Check where things stand"
  ],
  "vars": [
   "[Interviewer]"
  ]
 },
 {
  "n": 80,
  "slug": "build-the-interview-schedule-packet",
  "title": "Build the interview schedule packet",
  "prompt": "Write an email summary of the interview schedule for [Candidate], including their resume summary, interview dates, and who is interviewing them, ready to send to the attorneys.",
  "category": "Candidate sourcing",
  "theme": "Interview logistics",
  "jobs": [
   "Draft something"
  ],
  "vars": [
   "[Candidate]"
  ]
 },
 {
  "n": 82,
  "slug": "question-your-interview-volume",
  "title": "Question your interview volume",
  "prompt": "I need to conserve attorney and manager time on interviews. Help me find patterns where we're interviewing unqualified candidates who are immediately rejected.",
  "category": "Candidate sourcing",
  "theme": "Interview logistics",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 83,
  "slug": "calibrate-interview-evaluation-scores",
  "title": "Calibrate interview evaluation scores",
  "prompt": "Where do interview score distributions look abnormal?",
  "category": "Candidate sourcing",
  "theme": "Interview logistics",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 84,
  "slug": "find-summers-who-aren-t-getting-real-work",
  "title": "Find summers who aren't getting real work",
  "prompt": "Which summer associates have the fewest complete and active assignments?",
  "category": "Candidate sourcing",
  "theme": "The summer program",
  "jobs": [
   "Check where things stand"
  ],
  "vars": []
 },
 {
  "n": 85,
  "slug": "keep-a-pulse-on-work-allocation",
  "title": "Keep a pulse on work allocation",
  "prompt": "Summarize our project assignment distribution across summer associates.",
  "category": "Candidate sourcing",
  "theme": "The summer program",
  "jobs": [
   "Check where things stand"
  ],
  "vars": []
 },
 {
  "n": 86,
  "slug": "see-who-is-engaged-with-the-program",
  "title": "See who is engaged with the program",
  "prompt": "Which attorneys are overseeing the most summer program projects this year?",
  "category": "Candidate sourcing",
  "theme": "The summer program",
  "jobs": [
   "Check where things stand"
  ],
  "vars": []
 },
 {
  "n": 87,
  "slug": "find-the-assignments-that-develop-people",
  "title": "Find the assignments that develop people",
  "prompt": "Which projects have created the strongest development opportunities based on volume of feedback given?",
  "category": "Candidate sourcing",
  "theme": "The summer program",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 88,
  "slug": "spot-your-standout-summers",
  "title": "Spot your standout summers",
  "prompt": "Which summer associates have received excellent reviews, and what did reviewers specifically praise?",
  "category": "Candidate sourcing",
  "theme": "The summer program",
  "jobs": [
   "Find people or records"
  ],
  "vars": []
 },
 {
  "n": 90,
  "slug": "find-summers-missing-evaluations",
  "title": "Find summers missing evaluations",
  "prompt": "Which summer associates have not yet received program evaluations?",
  "category": "Candidate sourcing",
  "theme": "The summer program",
  "jobs": [
   "Check where things stand"
  ],
  "vars": []
 },
 {
  "n": 92,
  "slug": "find-themes-in-summer-program-evaluations",
  "title": "Find themes in summer program evaluations",
  "prompt": "What themes are coming through in our summer associate program evaluations this year? What are the differences by office?",
  "category": "Candidate sourcing",
  "theme": "The summer program",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 93,
  "slug": "match-summer-work-to-stated-interests",
  "title": "Match summer work to stated interests",
  "prompt": "Which summer associates have not been assigned work in a practice area they said they were interested in?",
  "category": "Candidate sourcing",
  "theme": "The summer program",
  "jobs": [
   "Find people or records"
  ],
  "vars": []
 },
 {
  "n": 94,
  "slug": "find-who-hasn-t-been-reviewed",
  "title": "Find who hasn't been reviewed",
  "prompt": "Show me every reviewee in the [Cycle] with no reviewers assigned or fewer than expected, plus any reviewer requests that never became a task.",
  "category": "Reviews and development",
  "theme": "Run the cycle",
  "jobs": [
   "Chase or follow up"
  ],
  "vars": [
   "[Cycle]"
  ]
 },
 {
  "n": 95,
  "slug": "thank-your-program-participants",
  "title": "Thank your program participants",
  "prompt": "Draft an email celebrating the attorneys who oversaw the most summer program projects, mentored the most summers, and left the most work assignment feedback.",
  "category": "Reviews and development",
  "theme": "Run the cycle",
  "jobs": [
   "Chase or follow up",
   "Draft something"
  ],
  "vars": []
 },
 {
  "n": 96,
  "slug": "find-missing-evaluations",
  "title": "Find missing evaluations",
  "prompt": "Show me everyone whose [Self Evaluation] has not been started.",
  "category": "Reviews and development",
  "theme": "Run the cycle",
  "jobs": [
   "Chase or follow up"
  ],
  "vars": [
   "[Self Evaluation]"
  ]
 },
 {
  "n": 97,
  "slug": "segment-your-reminder-list-precisely",
  "title": "Segment your reminder list precisely",
  "prompt": "Show me everyone who still owes a self-review but has either already completed their reviewer selections or isn't required to do them.",
  "category": "Reviews and development",
  "theme": "Run the cycle",
  "jobs": [
   "Chase or follow up"
  ],
  "vars": [],
  "req": "Requires a self-assessment stage in your review cycle."
 },
 {
  "n": 98,
  "slug": "group-participants-by-what-they-still-owe",
  "title": "Group participants by what they still owe",
  "prompt": "Split my review cycle participants into three groups: who has completed nothing yet, who is started but incomplete, and who is complete through all stages.",
  "category": "Reviews and development",
  "theme": "Run the cycle",
  "jobs": [
   "Chase or follow up"
  ],
  "vars": []
 },
 {
  "n": 99,
  "slug": "track-one-reviewee-s-review-status",
  "title": "Track one reviewee's review status",
  "prompt": "Show me the status of every review assigned for [Reviewee]: outstanding, submitted, or declined, and who owns each one.",
  "category": "Reviews and development",
  "theme": "Run the cycle",
  "jobs": [
   "Check where things stand"
  ],
  "vars": [
   "[Reviewee]"
  ]
 },
 {
  "n": 100,
  "slug": "catch-over-requesting",
  "title": "Catch over-requesting",
  "prompt": "Which reviewees have requested more reviewers than required, and how many extra requests did each one make?",
  "category": "Reviews and development",
  "theme": "Run the cycle",
  "jobs": [
   "Check where things stand"
  ],
  "vars": []
 },
 {
  "n": 101,
  "slug": "audit-reviewer-selections-for-fit",
  "title": "Audit reviewer selections for fit",
  "prompt": "Flag any reviewer selections where a junior associate has requested a senior partner who has little direct visibility into their work, based on matters.",
  "category": "Reviews and development",
  "theme": "Run the cycle",
  "jobs": [
   "Find people or records"
  ],
  "vars": [],
  "req": "Requires matters loaded into the review cycle."
 },
 {
  "n": 102,
  "slug": "handle-a-departure-mid-cycle",
  "title": "Handle a departure mid-cycle",
  "prompt": "Who has selected [Departing Attorney] as a reviewer?",
  "category": "Reviews and development",
  "theme": "Run the cycle",
  "jobs": [
   "Find people or records"
  ],
  "vars": [
   "[Departing Attorney]"
  ]
 },
 {
  "n": 103,
  "slug": "find-broken-reviewer-assignments",
  "title": "Find broken reviewer assignments",
  "prompt": "Which reviewees now have a matter with no valid reviewer assigned? Include their email addresses.",
  "category": "Reviews and development",
  "theme": "Run the cycle",
  "jobs": [
   "Chase or follow up"
  ],
  "vars": []
 },
 {
  "n": 104,
  "slug": "scan-a-cycle-for-risky-language",
  "title": "Scan a cycle for risky language",
  "prompt": "Scan every review written in the [Cycle] and flag any that contain inappropriate, potentially biased, or protected-class language.",
  "category": "Reviews and development",
  "theme": "Run the cycle",
  "jobs": [
   "Check where things stand"
  ],
  "vars": [
   "[Cycle]"
  ]
 },
 {
  "n": 105,
  "slug": "find-your-harshest-reviewer",
  "title": "Find your harshest reviewer",
  "prompt": "Of all the reviewers this cycle, who is the harshest? Show me who gives the lowest scores and the most critical narrative feedback.",
  "category": "Reviews and development",
  "theme": "Write and check a review",
  "jobs": [
   "Find people or records"
  ],
  "vars": [],
  "req": "Requires at least one rated question on your review."
 },
 {
  "n": 106,
  "slug": "separate-reviewer-severity-from-real-performance",
  "title": "Separate reviewer severity from real performance",
  "prompt": "Compare average review scores by reviewer within [Practice Group] and tell me whether low scores reflect performance or individual reviewer severity.",
  "category": "Reviews and development",
  "theme": "Write and check a review",
  "jobs": [
   "Draft something"
  ],
  "vars": [
   "[Practice Group]"
  ]
 },
 {
  "n": 107,
  "slug": "find-what-people-want-to-get-better-at",
  "title": "Find what people want to get better at",
  "prompt": "From the self-evaluations in [Cycle], what are the top five areas in which reviewees say they want to improve?",
  "category": "Reviews and development",
  "theme": "Development themes and training",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[Cycle]"
  ],
  "req": "Requires a self-assessment stage in your review cycle."
 },
 {
  "n": 108,
  "slug": "find-what-reviewers-keep-raising",
  "title": "Find what reviewers keep raising",
  "prompt": "What are the top five development themes reviewers raised about [Class Year] this cycle?",
  "category": "Reviews and development",
  "theme": "Write and check a review",
  "jobs": [
   "Draft something"
  ],
  "vars": [
   "[Class Year]"
  ]
 },
 {
  "n": 109,
  "slug": "turn-review-themes-into-a-training-plan",
  "title": "Turn review themes into a training plan",
  "prompt": "Read all reviews in [Cycle] and tell me what skill gaps each practice group has, so I can plan training.",
  "category": "Reviews and development",
  "theme": "Write and check a review",
  "jobs": [
   "Draft something"
  ],
  "vars": [
   "[Cycle]"
  ],
  "req": "Pro tip: keep practice area filled in on employee records."
 },
 {
  "n": 110,
  "slug": "set-development-goals-from-the-cycle",
  "title": "Set development goals from the cycle",
  "prompt": "At the close of the [Cycle], identify the most common areas of underperformance among [mid-level associates] and suggest development goals for each theme.",
  "category": "Reviews and development",
  "theme": "Write and check a review",
  "jobs": [
   "Draft something"
  ],
  "vars": [
   "[Cycle]",
   "[mid-level associates]"
  ]
 },
 {
  "n": 111,
  "slug": "announce-the-training-you-just-designed",
  "title": "Announce the training you just designed",
  "prompt": "Based on the development themes from [Cycle], write the announcement I'll send to associates describing the [training session] we're running to address them.",
  "category": "Reviews and development",
  "theme": "Reviewer patterns and calibration",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[Cycle]",
   "[training session]"
  ]
 },
 {
  "n": 112,
  "slug": "draft-a-consensus-review",
  "title": "Draft a consensus review",
  "prompt": "Summarize all reviews written about [Reviewee] this cycle into a single consensus write-up.",
  "category": "Reviews and development",
  "theme": "Reviewer patterns and calibration",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[Reviewee]"
  ]
 },
 {
  "n": 113,
  "slug": "build-a-documentation-record",
  "title": "Build a documentation record",
  "prompt": "Pull every individual review on [Attorney/Professional] over the last [2] years and summarize the performance concerns raised.",
  "category": "Reviews and development",
  "theme": "Reviewer patterns and calibration",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[Attorney/Professional]",
   "[2]"
  ]
 },
 {
  "n": 114,
  "slug": "gather-support-for-a-performance-plan",
  "title": "Gather support for a performance plan",
  "prompt": "[Attorney/Professional] is not performing and we're considering a performance plan. Pull the supporting review data and history I'd need to document it.",
  "category": "Reviews and development",
  "theme": "Reviewer patterns and calibration",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[Attorney/Professional]"
  ]
 },
 {
  "n": 115,
  "slug": "track-one-person-s-trajectory",
  "title": "Track one person's trajectory",
  "prompt": "Analyze [Attorney/Professional]'s reviews across all prior cycles and show me how the feedback has changed year over year.",
  "category": "Reviews and development",
  "theme": "Development themes and training",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[Attorney/Professional]"
  ]
 },
 {
  "n": 116,
  "slug": "find-the-feedback-nobody-wrote",
  "title": "Find the feedback nobody wrote",
  "prompt": "Show me which reviewees received only positive or non-substantive feedback this cycle, and which reviewers consistently avoid constructive comments.",
  "category": "Reviews and development",
  "theme": "Development themes and training",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 117,
  "slug": "get-a-single-cycle-status-view",
  "title": "Get a single cycle status view",
  "prompt": "Give me a single view of where the [Cycle] stands right now: completion by group, outstanding reviewers, and anything that needs my attention.",
  "category": "Reviews and development",
  "theme": "Development themes and training",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[Cycle]"
  ]
 },
 {
  "n": 119,
  "slug": "find-the-vague-parts-of-a-review",
  "title": "Find the vague parts of a review",
  "prompt": "Review this [evaluation] and tell me where I've been vague. Flag anywhere I should add a specific example.",
  "category": "Reviews and development",
  "theme": "Development themes and training",
  "jobs": [
   "Draft something"
  ],
  "vars": [
   "[evaluation]"
  ]
 },
 {
  "n": 120,
  "slug": "check-reviews-for-risk",
  "title": "Check reviews for risk",
  "prompt": "Check reviews for language that could create an HR concern or sound unprofessional.",
  "category": "Reviews and development",
  "theme": "Development themes and training",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 121,
  "slug": "find-what-separates-your-top-performers",
  "title": "Find what separates your top performers",
  "prompt": "What skills separate our top-performing [third-year associates]?",
  "category": "Reviews and development",
  "theme": "Development themes and training",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[third-year associates]"
  ]
 },
 {
  "n": 122,
  "slug": "track-skills-across-the-firm",
  "title": "Track skills across the firm",
  "prompt": "What skills are improving across the firm this cycle, and what skills are getting worse?",
  "category": "Reviews and development",
  "theme": "Development themes and training",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 123,
  "slug": "find-who-is-improving-and-who-is-stuck",
  "title": "Find who is improving and who is stuck",
  "prompt": "Which associates are improving the fastest, and which may be plateauing?",
  "category": "Reviews and development",
  "theme": "One person's record",
  "jobs": [
   "Find people or records"
  ],
  "vars": []
 },
 {
  "n": 124,
  "slug": "find-feedback-that-keeps-repeating",
  "title": "Find feedback that keeps repeating",
  "prompt": "What developmental feedback is repeated year after year for the same people?",
  "category": "Reviews and development",
  "theme": "One person's record",
  "jobs": [
   "Find people or records"
  ],
  "vars": []
 },
 {
  "n": 125,
  "slug": "plan-next-quarter-s-training",
  "title": "Plan next quarter's training",
  "prompt": "Based on review data, what firm-wide training should we run next quarter? Which practice groups have the biggest [writing] gaps, and which offices need [deposition] training?",
  "category": "Reviews and development",
  "theme": "One person's record",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[writing]",
   "[deposition]"
  ],
  "req": "Pro tip: keep practice area filled in on employee records."
 },
 {
  "n": 127,
  "slug": "find-your-most-useful-reviewers",
  "title": "Find your most useful reviewers",
  "prompt": "Which reviewers provide the most actionable feedback? Which focus mostly on technical skills versus soft skills?",
  "category": "Reviews and development",
  "theme": "Performance decisions",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [],
  "req": "Requires at least one rated question on your review."
 },
 {
  "n": 128,
  "slug": "find-reviewers-who-break-from-consensus",
  "title": "Find reviewers who break from consensus",
  "prompt": "Which reviewers disagree most with the consensus?",
  "category": "Reviews and development",
  "theme": "Performance decisions",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [],
  "req": "Requires at least one rated question on your review."
 },
 {
  "n": 130,
  "slug": "recognize-sustained-improvement",
  "title": "Recognize sustained improvement",
  "prompt": "Who has demonstrated sustained improvement over three years of performance reviews?",
  "category": "Reviews and development",
  "theme": "Performance decisions",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 131,
  "slug": "show-hours-in-context",
  "title": "Show hours in context",
  "prompt": "Show me [Attorney]'s total hours for the review period broken out by matter, and how they're trending against their class year.",
  "category": "Reviews and development",
  "theme": "Performance decisions",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[Attorney]"
  ]
 },
 {
  "n": 132,
  "slug": "send-performance-signal-back-to-recruiting",
  "title": "Send performance signal back to recruiting",
  "prompt": "What performance trends should we be bringing back to the recruiting team to inform how they evaluate candidates?",
  "category": "Firm-wide talent strategy",
  "theme": "",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 133,
  "slug": "look-across-recruiting-and-performance-evaluations",
  "title": "Look across recruiting and performance evaluations",
  "prompt": "Do our interview evaluations and performance reviews touch on similar behavioral and technical skills? Outline the overlap and differences.",
  "category": "Firm-wide talent strategy",
  "theme": "",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 134,
  "slug": "compare-two-law-schools-from-recruiting-to-performance",
  "title": "Compare two law schools, from recruiting to performance",
  "prompt": "Compare [School A] and [School B] for our student hiring: offers, acceptances, and how those hires have performed since.",
  "category": "Firm-wide talent strategy",
  "theme": "",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[School A]",
   "[School B]"
  ]
 },
 {
  "n": 136,
  "slug": "find-flight-risk",
  "title": "Find flight risk",
  "prompt": "Which [Attorneys/Professionals] show signals worth a check-in: low or declining review ratings, thin self-reviews, or feedback themes suggesting disengagement? Label each as a signal rather than a prediction.",
  "category": "Firm-wide talent strategy",
  "theme": "",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[Attorneys/Professionals]"
  ],
  "req": "Requires at least one rated question on your review."
 },
 {
  "n": 137,
  "slug": "compare-groups-directly",
  "title": "Compare groups directly",
  "prompt": "Compare review themes, especially regarding workload and rigor, between [Practice Group A] and [Practice Group B].",
  "category": "Firm-wide talent strategy",
  "theme": "",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[Practice Group A]",
   "[Practice Group B]"
  ],
  "req": "Pro tip: keep practice area filled in on employee records."
 },
 {
  "n": 138,
  "slug": "find-what-your-stayers-share",
  "title": "Find what your stayers share",
  "prompt": "What do our longest-tenured [Attorneys/Professionals] have in common, based on start date, work history, education history, and feedback themes?",
  "category": "Firm-wide talent strategy",
  "theme": "",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[Attorneys/Professionals]"
  ]
 },
 {
  "n": 139,
  "slug": "look-for-early-warning-language",
  "title": "Look for early warning language",
  "prompt": "Which recent review comments contain language suggesting disengagement or uncertainty about staying?",
  "category": "Firm-wide talent strategy",
  "theme": "",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 140,
  "slug": "get-the-full-department-picture",
  "title": "Get the full department picture",
  "prompt": "Give me a summary of activity in [Department] across recruiting and performance cycles.",
  "category": "Firm-wide talent strategy",
  "theme": "",
  "jobs": [
   "Check where things stand"
  ],
  "vars": [
   "[Department]"
  ],
  "req": "Pro tip: Keep your [Department] options up to date."
 },
 {
  "n": 141,
  "slug": "pose-your-biggest-questions",
  "title": "Pose your biggest questions",
  "prompt": "What should I be worried about right now across our talent data?",
  "category": "Firm-wide talent strategy",
  "theme": "",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 142,
  "slug": "look-for-patterns-people-would-miss",
  "title": "Look for patterns people would miss",
  "prompt": "What patterns are emerging in our talent data that humans might miss?",
  "category": "Firm-wide talent strategy",
  "theme": "",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 143,
  "slug": "ask-what-changed",
  "title": "Ask what changed",
  "prompt": "What changed since last year across recruiting and performance?",
  "category": "Firm-wide talent strategy",
  "theme": "",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 144,
  "slug": "find-who-deserves-recognition",
  "title": "Find who deserves recognition",
  "prompt": "Which [Department] professionals should receive special recognition this year based on their reviews?",
  "category": "Firm-wide talent strategy",
  "theme": "",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [
   "[Department]"
  ],
  "req": "Pro tip: Keep your [Department] options up to date in Organization Settings."
 },
 {
  "n": 146,
  "slug": "name-the-top-risks",
  "title": "Name the top risks",
  "prompt": "Suggest the five biggest talent risks in the firm right now, with the evidence behind each one.",
  "category": "Firm-wide talent strategy",
  "theme": "",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 149,
  "slug": "explore-areas-of-impact",
  "title": "Explore areas of impact",
  "prompt": "If we changed only one thing about our talent strategy this year, what would have the biggest impact?",
  "category": "Firm-wide talent strategy",
  "theme": "",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": []
 },
 {
  "n": 150,
  "slug": "find-growth-to-celebrate",
  "title": "Find growth to celebrate",
  "prompt": "Which practice group is improving the fastest, based on review ratings and feedback themes across cycles?",
  "category": "Firm-wide talent strategy",
  "theme": "",
  "jobs": [
   "Compare or spot a pattern"
  ],
  "vars": [],
  "req": "Pro tip: keep practice area filled in on employee records."
 }
];


export const CATEGORIES = ["Lateral and partner hiring","Candidate sourcing","Reviews and development","Firm-wide talent strategy"];

export const THEMES = {
 "Lateral and partner hiring": [
  "Where the pipeline stands",
  "Look up a candidate",
  "Agencies and search firms",
  "Speed, timing, and trends",
  "Interviewing and feedback",
  "Write it up",
  "Screening criteria",
  "Recurring reporting"
 ],
 "Candidate sourcing": [
  "Run an event",
  "Who you met",
  "Interest and follow-up lists",
  "What events and schools produce",
  "Interview logistics",
  "Student screening",
  "The summer program"
 ],
 "Reviews and development": [
  "Run the cycle",
  "Write and check a review",
  "Reviewer patterns and calibration",
  "Development themes and training",
  "One person's record",
  "Performance decisions"
 ],
 "Firm-wide talent strategy": []
};

export const JOBS = ["Find people or records","Check where things stand","Compare or spot a pattern","Chase or follow up","Draft something"];

export const CATEGORY_NOTES = {
 "Lateral and partner hiring": "Lateral, partner and associate hiring: status, agencies, interviewers, scores.",
 "Candidate sourcing": "Student pipelines end to end: campus events, screening, interview logistics, the summer program.",
 "Reviews and development": "Calibration, reviewer patterns, and the development themes running through your written reviews.",
 "Firm-wide talent strategy": "Recruiting and performance read together: hiring efficacy, retention, promotion, risk."
};

export const JOB_NOTES = {
 "Find people or records": "Pull a specific set of candidates, students or attorneys out of the pile.",
 "Check where things stand": "The current state of a pipeline, a cycle or one person.",
 "Compare or spot a pattern": "Counts, trends and correlations across your own records.",
 "Chase or follow up": "See what is outstanding and who is holding it up.",
 "Draft something": "Get a first draft of the email, memo, packet or announcement."
};

export const slugify = s => String(s).toLowerCase().replace(/&/g,"and").replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"");
