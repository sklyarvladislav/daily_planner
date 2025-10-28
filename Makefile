compose:
	docker build -t "dailyplanner:1" .
	docker run -d --rm --name="Daily_planner" dailyplanner:1
	
down:
	docker stop Daily_planner

