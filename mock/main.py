from fastapi import FastAPI, HTTPException

app = FastAPI()


@app.post("/2/tweets")
async def root():
    return {
        "data": {
            "id": "1445880548472328192",
            "text": "Are you excited for the weekend?"
        }
    }


@app.get("/2/users/{user}/tweets")
async def root(user):
    return {
        "data": [
            {
                "id": "1338971066773905408",
                "edit_history_tweet_ids": [
                    "1338971066773905408"
                ],
                "text": "💡 Using Twitter data for academic research? Join our next livestream this Friday @ 9am PT on https://t.co/GrtBOXh5Y1!n n@SuhemParack will show how to get started with recent search &amp; filtered stream endpoints on the #TwitterAPI v2, the new Tweet payload, annotations, &amp; more. https://t.co/IraD2Z7wEg"
            },
        ],
        "meta": {
            "oldest_id": "1334564488884862976",
            "newest_id": "1338971066773905408",
            "result_count": 10,
            "next_token": "7140dibdnow9c7btw3w29grvxfcgvpb9n9coehpk7xz5i"
        }
    }


@app.get("/2/users/me")
async def root():
    return {
        "data": {
            "id": "2244994945",
            "name": "TwitterDev",
            "username": "Twitter Dev"
        }
    }


@app.post("/2/users/{user}/retweets")
async def root(user):
    return {
        "data": {
            "retweeted": True
        }
    }


@app.post("/token/oauth/")
async def root():
    return {
        "access_token": "not_a_real_token",
        "token_type": "Bearer",
        "expires_in": 7200,
    }


@app.get("/open_api/ecowatt/v4/signals")
async def root():
    return {
        "signals": [
            {
                "GenerationFichier": "2022-06-04T07:36:25+02:00",
                "jour": "2022-06-06T00:00:00+02:00",
                "dvalue": 1,
                "message": "Situation normale. ",
                "values": [
                    {
                        "pas": 0,
                        "hvalue": 1
                    },
                    {
                        "pas": 1,
                        "hvalue": 1
                    },
                    {
                        "pas": 2,
                        "hvalue": 1
                    },
                    {
                        "pas": 3,
                        "hvalue": 1
                    },
                    {
                        "pas": 4,
                        "hvalue": 1
                    },
                    {
                        "pas": 5,
                        "hvalue": 1
                    },
                    {
                        "pas": 6,
                        "hvalue": 1
                    },
                    {
                        "pas": 7,
                        "hvalue": 1
                    },
                    {
                        "pas": 8,
                        "hvalue": 1
                    },
                    {
                        "pas": 9,
                        "hvalue": 1
                    },
                    {
                        "pas": 10,
                        "hvalue": 1
                    },
                    {
                        "pas": 11,
                        "hvalue": 1
                    },
                    {
                        "pas": 12,
                        "hvalue": 1
                    },
                    {
                        "pas": 13,
                        "hvalue": 1
                    },
                    {
                        "pas": 14,
                        "hvalue": 1
                    },
                    {
                        "pas": 15,
                        "hvalue": 1
                    },
                    {
                        "pas": 16,
                        "hvalue": 1
                    },
                    {
                        "pas": 17,
                        "hvalue": 1
                    },
                    {
                        "pas": 18,
                        "hvalue": 1
                    },
                    {
                        "pas": 19,
                        "hvalue": 1
                    },
                    {
                        "pas": 20,
                        "hvalue": 1
                    },
                    {
                        "pas": 21,
                        "hvalue": 1
                    },
                    {
                        "pas": 22,
                        "hvalue": 1
                    },
                    {
                        "pas": 23,
                        "hvalue": 1
                    }
                ]
            },
            {
                "GenerationFichier": "2022-06-03T07:36:25+02:00",
                "jour": "2022-06-04T00:00:00+02:00",
                "dvalue": 3,
                "message": "Coupures d'électricité programmées",
                "values": [
                    {
                        "pas": 0,
                        "hvalue": 1
                    },
                    {
                        "pas": 1,
                        "hvalue": 1
                    },
                    {
                        "pas": 2,
                        "hvalue": 1
                    },
                    {
                        "pas": 3,
                        "hvalue": 1
                    },
                    {
                        "pas": 4,
                        "hvalue": 1
                    },
                    {
                        "pas": 5,
                        "hvalue": 2
                    },
                    {
                        "pas": 6,
                        "hvalue": 2
                    },
                    {
                        "pas": 7,
                        "hvalue": 3
                    },
                    {
                        "pas": 8,
                        "hvalue": 3
                    },
                    {
                        "pas": 9,
                        "hvalue": 3
                    },
                    {
                        "pas": 10,
                        "hvalue": 3
                    },
                    {
                        "pas": 11,
                        "hvalue": 3
                    },
                    {
                        "pas": 12,
                        "hvalue": 3
                    },
                    {
                        "pas": 13,
                        "hvalue": 2
                    },
                    {
                        "pas": 14,
                        "hvalue": 2
                    },
                    {
                        "pas": 15,
                        "hvalue": 2
                    },
                    {
                        "pas": 16,
                        "hvalue": 2
                    },
                    {
                        "pas": 17,
                        "hvalue": 3
                    },
                    {
                        "pas": 18,
                        "hvalue": 3
                    },
                    {
                        "pas": 19,
                        "hvalue": 3
                    },
                    {
                        "pas": 20,
                        "hvalue": 2
                    },
                    {
                        "pas": 21,
                        "hvalue": 2
                    },
                    {
                        "pas": 22,
                        "hvalue": 2
                    },
                    {
                        "pas": 23,
                        "hvalue": 2
                    }
                ]
            },
            {
                "GenerationFichier": "2022-06-03T07:36:25+02:00",
                "jour": "2022-06-05T00:00:00+02:00",
                "dvalue": 2,
                "message": "Risque de coupures d'électricité",
                "values": [
                    {
                        "pas": 0,
                        "hvalue": 1
                    },
                    {
                        "pas": 1,
                        "hvalue": 1
                    },
                    {
                        "pas": 2,
                        "hvalue": 1
                    },
                    {
                        "pas": 3,
                        "hvalue": 1
                    },
                    {
                        "pas": 4,
                        "hvalue": 1
                    },
                    {
                        "pas": 5,
                        "hvalue": 1
                    },
                    {
                        "pas": 6,
                        "hvalue": 1
                    },
                    {
                        "pas": 7,
                        "hvalue": 2
                    },
                    {
                        "pas": 8,
                        "hvalue": 2
                    },
                    {
                        "pas": 9,
                        "hvalue": 2
                    },
                    {
                        "pas": 10,
                        "hvalue": 2
                    },
                    {
                        "pas": 11,
                        "hvalue": 2
                    },
                    {
                        "pas": 12,
                        "hvalue": 1
                    },
                    {
                        "pas": 13,
                        "hvalue": 1
                    },
                    {
                        "pas": 14,
                        "hvalue": 1
                    },
                    {
                        "pas": 15,
                        "hvalue": 1
                    },
                    {
                        "pas": 16,
                        "hvalue": 1
                    },
                    {
                        "pas": 17,
                        "hvalue": 2
                    },
                    {
                        "pas": 18,
                        "hvalue": 2
                    },
                    {
                        "pas": 19,
                        "hvalue": 1
                    },
                    {
                        "pas": 20,
                        "hvalue": 1
                    },
                    {
                        "pas": 21,
                        "hvalue": 1
                    },
                    {
                        "pas": 22,
                        "hvalue": 1
                    },
                    {
                        "pas": 23,
                        "hvalue": 1
                    }
                ]
            },
            {
                "GenerationFichier": "2022-06-03T07:36:25+02:00",
                "jour": "2022-06-03T00:00:00+02:00",
                "dvalue": 3,
                "message": "Coupures d'électricité en cours",
                "values": [
                    {
                        "pas": 7,
                        "hvalue": 3
                    },
                    {
                        "pas": 8,
                        "hvalue": 3
                    },
                    {
                        "pas": 9,
                        "hvalue": 1
                    },
                    {
                        "pas": 10,
                        "hvalue": 1
                    },
                    {
                        "pas": 11,
                        "hvalue": 1
                    },
                    {
                        "pas": 12,
                        "hvalue": 1
                    },
                    {
                        "pas": 13,
                        "hvalue": 1
                    },
                    {
                        "pas": 14,
                        "hvalue": 3
                    },
                    {
                        "pas": 15,
                        "hvalue": 3
                    },
                    {
                        "pas": 16,
                        "hvalue": 3
                    },
                    {
                        "pas": 17,
                        "hvalue": 3
                    },
                    {
                        "pas": 18,
                        "hvalue": 3
                    },
                    {
                        "pas": 19,
                        "hvalue": 3
                    },
                    {
                        "pas": 20,
                        "hvalue": 3
                    },
                    {
                        "pas": 21,
                        "hvalue": 2
                    },
                    {
                        "pas": 22,
                        "hvalue": 2
                    },
                    {
                        "pas": 23,
                        "hvalue": 2
                    }
                ]
            }
        ]
    }
