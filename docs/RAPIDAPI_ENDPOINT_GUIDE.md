get user by username
const url = 'https://twitter241.p.rapidapi.com/user?username=MrBeast';
const options = {
	method: 'GET',
	headers: {
		'x-rapidapi-key': '',
		'x-rapidapi-host': 'twitter241.p.rapidapi.com'
	}
};

try {
	const response = await fetch(url, options);
	const result = await response.text();
	console.log(result);
} catch (error) {
	console.error(error);
}
---
get users by IDs
const url = 'https://twitter241.p.rapidapi.com/user';
const options = {
	method: 'GET',
	headers: {
		'Content-Type': 'application/json'
	}
};

try {
	const response = await fetch(url, options);
	const result = await response.text();
	console.log(result);
} catch (error) {
	console.error(error);
}
---
get users by IDs v2
const url = 'https://twitter241.p.rapidapi.com/get-users-v2?users=1222790936679206913%2C133938408%2C34186021';
const options = {
	method: 'GET',
	headers: {
		'x-rapidapi-key': '',
		'x-rapidapi-host': 'twitter241.p.rapidapi.com'
	}
};

try {
	const response = await fetch(url, options);
	const result = await response.text();
	console.log(result);
} catch (error) {
	console.error(error);
}
---
get available trends locations
const url = 'https://twitter241.p.rapidapi.com/trends-locations';
const options = {
	method: 'GET',
	headers: {
		'x-rapidapi-key': '',
		'x-rapidapi-host': 'twitter241.p.rapidapi.com'
	}
};

try {
	const response = await fetch(url, options);
	const result = await response.text();
	console.log(result);
} catch (error) {
	console.error(error);
}
---
get trends by location
const url = 'https://twitter241.p.rapidapi.com/trends-by-location?woeid=2424766';
const options = {
	method: 'GET',
	headers: {
		'x-rapidapi-key': '',
		'x-rapidapi-host': 'twitter241.p.rapidapi.com'
	}
};

try {
	const response = await fetch(url, options);
	const result = await response.text();
	console.log(result);
} catch (error) {
	console.error(error);
}
---
get user tweets
const url = 'https://twitter241.p.rapidapi.com/user-tweets?user=2455740283&count=20';
const options = {
	method: 'GET',
	headers: {
		'x-rapidapi-key': '',
		'x-rapidapi-host': 'twitter241.p.rapidapi.com'
	}
};

try {
	const response = await fetch(url, options);
	const result = await response.text();
	console.log(result);
} catch (error) {
	console.error(error);
}
---
search twitter v3
const url = 'https://twitter241.p.rapidapi.com/search-v3?type=Top&count=20&query=MrBeast';
const options = {
	method: 'GET',
	headers: {
		'x-rapidapi-key': '',
		'x-rapidapi-host': 'twitter241.p.rapidapi.com'
	}
};

try {
	const response = await fetch(url, options);
	const result = await response.text();
	console.log(result);
} catch (error) {
	console.error(error);
}
---
get tweets details by IDs v2
const url = 'https://twitter241.p.rapidapi.com/tweet-by-ids-v2?tweetIds=1892702078029476328%2C1885213980739711144%2C1886671728941924567%2C1905285543136551299';
const options = {
	method: 'GET',
	headers: {
		'x-rapidapi-key': '',
		'x-rapidapi-host': 'twitter241.p.rapidapi.com'
	}
};

try {
	const response = await fetch(url, options);
	const result = await response.text();
	console.log(result);
} catch (error) {
	console.error(error);
}
---
get tweets details v2
const url = 'https://twitter241.p.rapidapi.com/tweet-v2?pid=1631781099415257088';
const options = {
	method: 'GET',
	headers: {
		'x-rapidapi-key': '',
		'x-rapidapi-host': 'twitter241.p.rapidapi.com'
	}
};

try {
	const response = await fetch(url, options);
	const result = await response.text();
	console.log(result);
} catch (error) {
	console.error(error);
}
---
get user followings
const url = 'https://twitter241.p.rapidapi.com/followings?user=2455740283&count=20';
const options = {
	method: 'GET',
	headers: {
		'x-rapidapi-key': '',
		'x-rapidapi-host': 'twitter241.p.rapidapi.com'
	}
};

try {
	const response = await fetch(url, options);
	const result = await response.text();
	console.log(result);
} catch (error) {
	console.error(error);
}
---
get user followers
const url = 'https://twitter241.p.rapidapi.com/followers?user=2455740283&count=20';
const options = {
	method: 'GET',
	headers: {
		'x-rapidapi-key': '',
		'x-rapidapi-host': 'twitter241.p.rapidapi.com'
	}
};

try {
	const response = await fetch(url, options);
	const result = await response.text();
	console.log(result);
} catch (error) {
	console.error(error);
}
