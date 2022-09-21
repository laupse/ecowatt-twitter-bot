use chrono::{DateTime, Local};
use oauth2::basic::BasicClient;
use oauth2::reqwest::http_client;
use oauth2::AccessToken;
use oauth2::TokenResponse;
use oauth2::{AuthUrl, ClientId, ClientSecret, TokenUrl};
use reqwest::blocking::Client;
use reqwest::{self, StatusCode};
use serde::Deserialize;
use serde::Serialize;

#[derive(Debug, Clone)]
pub struct TokenRetrievalError;

#[derive(Debug, Clone)]
pub enum SignalsRetrievalError {
    HttpError(Option<StatusCode>),
    NoneHttpError(String),
}
#[derive(Serialize, Deserialize, Debug)]
pub struct ApiResponse {
    signals: Vec<Signal>,
    #[serde(skip_deserializing)]
    pub latest_generation_fichier: DateTime<Local>,
}

#[derive(Serialize, Deserialize, Debug)]
struct Signal {
    #[serde(rename(deserialize = "GenerationFichier"))]
    generation_fichier: DateTime<Local>,
    jour: DateTime<Local>,
    #[serde(skip_deserializing)]
    formatted_jour: String,
    dvalue: u8,
    message: String,
    values: Vec<Value>,
}

#[derive(Serialize, Deserialize, Debug)]
struct Value {
    pas: u8,
    hvalue: u8,
}

pub struct RteClient {
    oauth2: oauth2::basic::BasicClient,
    client: reqwest::blocking::Client,
    url: String,
}

impl RteClient {
    pub fn new(base_url: String, client_id: String, client_secret: String) -> RteClient {
        let client = Client::new();
        let oauth2 = BasicClient::new(
            ClientId::new(client_id),
            Some(ClientSecret::new(client_secret)),
            AuthUrl::new("http://authorize".to_string()).expect("Expect correct url"),
            Some(
                TokenUrl::new(String::from(base_url.to_owned() + "/token/oauth/"))
                    .expect("Expect correct url"),
            ),
        );
        RteClient {
            oauth2,
            client,
            url: base_url + "/open_api/ecowatt/v4/signals",
        }
    }

    fn get_token(&self) -> Result<AccessToken, TokenRetrievalError> {
        let response = self
            .oauth2
            .exchange_client_credentials()
            .request(http_client)
            .map_err(|_| TokenRetrievalError)?;
        Ok(response.access_token().to_owned())
    }

    pub fn fetch_signals(&self) -> Result<ApiResponse, SignalsRetrievalError> {
        let token = self.get_token().map_err(|_| {
            SignalsRetrievalError::NoneHttpError(String::from("Token retrieval error"))
        })?;

        let mut result = self
            .client
            .get(self.url.clone())
            .bearer_auth(token.secret())
            .send()
            .map_err(|err| SignalsRetrievalError::NoneHttpError(err.to_string()))?
            .error_for_status()
            .map_err(|err| SignalsRetrievalError::HttpError(err.status()))?
            .json::<ApiResponse>()
            .map_err(|err| SignalsRetrievalError::NoneHttpError(err.to_string()))?;

        //Compute the relative number of day with today
        result
            .signals
            .iter_mut()
            .for_each(|f| f.formatted_jour = f.jour.date_naive().format("%d/%m/%Y").to_string());

        // find the date from the latest change
        if let Some(signal) = result.signals.iter().max_by_key(|f| f.generation_fichier) {
            result.latest_generation_fichier = signal.generation_fichier
        }

        //And then sort it by this relative number
        result.signals.sort_by_key(|k| k.jour);
        Ok(result)
    }
}
