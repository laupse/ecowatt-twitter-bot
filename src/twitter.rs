use log::debug;
use serde::Serialize;
use tera::{Context, Tera};

use crate::rte::ApiResponse;
use reqwest::{blocking::Client, header::AUTHORIZATION, StatusCode};

#[derive(Debug, Clone)]
pub enum PostTweetError {
    RenderTweetError(String),
    HttpError(Option<StatusCode>),
    NoneHttpError(String),
}

#[derive(oauth::Request, Serialize)]
struct Tweet {
    text: String,
}

pub struct TweetClient {
    client: reqwest::blocking::Client,
    tera: tera::Tera,
    url: String,
    client_id: String,
    client_secret: String,
    token: String,
    token_secret: String,
}

impl TweetClient {
    pub fn new(
        url: String,
        client_id: String,
        client_secret: String,
        token: String,
        token_secret: String,
        tweet_template: String,
    ) -> TweetClient {
        let client = Client::new();
        let mut tera = Tera::default();
        tera.add_template_file(tweet_template, Some("tweet"))
            .expect("template should be parsable");

        TweetClient {
            client,
            tera,
            url,
            client_id,
            client_secret,
            token,
            token_secret,
        }
    }

    fn generate_authorization_header(&self) -> String {
        let token = oauth::Token::from_parts(
            &self.client_id,
            &self.client_secret,
            &self.token,
            &self.token_secret,
        );

        // Create the `Authorization` header.
        oauth::post(&self.url, &{}, &token, oauth::HMAC_SHA1)
    }
    pub fn send_tweet(&self, result: &ApiResponse) -> Result<(), PostTweetError> {
        let mut context = Context::from_serialize(&result)
            .map_err(|err| PostTweetError::NoneHttpError(err.to_string()))?;

        context.insert(
            "date",
            &result
                .latest_generation_fichier
                .format("%d/%m/%y %H:%M")
                .to_string(),
        );
        let tweet = &self
            .tera
            .render("tweet", &context)
            .map_err(|err| PostTweetError::NoneHttpError(err.to_string()))?;

        let authorization_header = &self.generate_authorization_header();
        let request = Tweet {
            text: tweet.to_string(),
        };
        debug!("{}", request.text);
        let _ = &self
            .client
            .post(&self.url)
            .json(&request)
            .header(AUTHORIZATION, authorization_header)
            .send()
            .map_err(|err| PostTweetError::NoneHttpError(err.to_string()))?
            .error_for_status()
            .map_err(|err| PostTweetError::HttpError(err.status()))?;
        Ok(())
    }
}
