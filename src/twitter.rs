use log::{debug, error};
use oauth::Request;
use serde::{Deserialize, Serialize};

use tera::{Context, Tera};

use crate::rte::ApiResponse;
use reqwest::{
    blocking::{Client, Response},
    header::AUTHORIZATION,
    Method, StatusCode,
};

#[derive(Debug, Clone)]
pub enum TwitterClientError {
    RenderTweetError(String),
    HttpError(Option<StatusCode>),
    NoneHttpError(String),
}

#[derive(oauth::Request, Serialize)]
struct Tweet {
    text: String,
}

#[derive(oauth::Request, Serialize)]
struct Retweet {
    tweet_id: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct TwitterResponse<D> {
    pub data: D,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct PostTweetResponse {
    pub id: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct UserResponse {
    pub id: String,
    pub name: String,
    pub username: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct UserTweetsResponse {
    pub id: String,
}

#[derive(Clone)]
pub struct TweetClient {
    client: reqwest::blocking::Client,
    tera: tera::Tera,
    base_url: String,
    client_id: String,
    client_secret: String,
    token: String,
    token_secret: String,
}

impl TweetClient {
    pub fn new(
        base_url: String,
        client_id: String,
        client_secret: String,
        token: String,
        token_secret: String,
        prevision_tweet_template: String,
        daily_prevision_tweet_template: String,
    ) -> TweetClient {
        let client = Client::new();
        let mut tera = Tera::default();
        tera.add_template_file(prevision_tweet_template, Some("prevision_tweet"))
            .expect("template should be parsable");

        tera.add_template_file(
            daily_prevision_tweet_template,
            Some("daily_prevision_tweet"),
        )
        .expect("template should be parsable");

        TweetClient {
            client,
            tera,
            base_url,
            client_id,
            client_secret,
            token,
            token_secret,
        }
    }

    fn generate_authorization_header<R>(&self, method: &Method, url: &String, request: R) -> String
    where
        R: Request,
    {
        let token = oauth::Token::from_parts(
            &self.client_id,
            &self.client_secret,
            &self.token,
            &self.token_secret,
        );

        // Create the `Authorization` header.
        oauth::authorize(method.as_str(), url, &request, &token, oauth::HMAC_SHA1)
    }

    fn do_request<R: oauth::Request, T: Serialize + ?Sized>(
        &self,
        method: Method,
        url: &String,
        params: &R,
        body: &T,
    ) -> Result<Response, TwitterClientError> {
        let authorization_header = self.generate_authorization_header(&method, &url, params);
        let response = self
            .client
            .request(method, url)
            .json(body)
            .header(AUTHORIZATION, authorization_header)
            .send()
            .map_err(|err| TwitterClientError::NoneHttpError(err.to_string()))?;

        let status = response.status();
        if status != 200 {
            error!("Request failed with {:?}", status);
            match response.text() {
                Ok(text) => debug!("{}", text),
                Err(err) => debug!("Could not read response {:?}", err),
            };
            return Err(TwitterClientError::HttpError(Some(status)));
        }

        Ok(response)
    }

    fn send_tweet(
        &self,
        content: String,
    ) -> Result<TwitterResponse<PostTweetResponse>, TwitterClientError> {
        debug!("{}", content);
        let request = Tweet { text: content };

        let full_url = String::from(&self.base_url) + "/tweets";
        let result = self.do_request(Method::POST, &full_url, &{}, &request)?;

        match result.json::<TwitterResponse<PostTweetResponse>>() {
            Ok(resp) => Ok(resp),
            Err(err) => Err(TwitterClientError::NoneHttpError(err.to_string())),
        }
    }

    pub fn render_then_send_tweet(
        &self,
        context: Context,
        template: &str,
    ) -> Result<(), TwitterClientError> {
        let tweet = self
            .tera
            .render(template, &context)
            .map_err(|err| TwitterClientError::RenderTweetError(err.to_string()))?;

        let _ = &self.send_tweet(tweet)?;

        Ok(())
    }

    pub fn send_tweets(&self, result: &ApiResponse) -> Result<(), TwitterClientError> {
        let context = Context::from_serialize(result)
            .map_err(|err| TwitterClientError::RenderTweetError(err.to_string()))?;

        self.render_then_send_tweet(context, "prevision_tweet")?;

        for signal in result.signals.iter() {
            if signal.dvalue > 1 {
                let mut hvalues = vec![0; 24];
                for hvalue in signal.values.iter() {
                    hvalues[hvalue.pas as usize] = hvalue.hvalue
                }
                let mut context = Context::new();
                context.insert("date", &signal.formatted_jour);
                context.insert("dvalue", &signal.dvalue);
                context.insert("hvalues", &hvalues);

                self.render_then_send_tweet(context, "daily_prevision_tweet")?;
            }
        }

        Ok(())
    }

    pub fn retweet_last(&self) -> Result<(), TwitterClientError> {
        let me_url = String::from(&self.base_url) + "/users/me";
        let me = self
            .do_request(Method::GET, &me_url, &{}, &{})?
            .json::<TwitterResponse<UserResponse>>()
            .map_err(|err| TwitterClientError::NoneHttpError(err.to_string()))?;

        let tweets_url =
            String::from(&self.base_url) + format!("/users/{}/tweets", me.data.id).as_str();
        let last_tweet = self
            .do_request(Method::GET, &tweets_url, &{}, &[("max_results", 1)])?
            .json::<TwitterResponse<Vec<UserTweetsResponse>>>()
            .map_err(|err| TwitterClientError::NoneHttpError(err.to_string()))?
            .data
            .pop();

        if let Some(tweet) = last_tweet {
            let retweets_url =
                String::from(&self.base_url) + format!("/users/{}/retweets", me.data.id).as_str();
            let request_retweet = Retweet { tweet_id: tweet.id };
            let _ = self.do_request(Method::POST, &retweets_url, &{}, &request_retweet)?;
        }

        Ok(())
    }
}
