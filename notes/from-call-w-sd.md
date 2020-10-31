- What is the URL for getting election results?
- What query string parameters does this resource support?
- What authentication is required?
- What is the format of the response?
		- Can we have a sample response?
- What is the rate limit for making requests for getting the XML? Or otherwise, how frequently should we request it?

Teegan Glasheen, Communications
Michael Vu,
Andrew M
Ashley Raja

## Changes

- Mail vs Polls details tables
- "Precinct reported" turned off
- First report out will include scanned ballots
- 235 polling location, 572? precincts consolidated into those places
- Will also display qualified write-ins
- Code to the RaceID in the XML tool
	- Need to explain
- 2pm estimated time to finish counting
- So it's a guess of the ballots you have, it doesn't include the number you might still get
- The RaceIDs and ContestantIDs in this test XML will be the same in the production XML?
- No need to use `<PrecReported>`, will remain zero
- `<ElectionDay>`<PollsBallotsVotes>