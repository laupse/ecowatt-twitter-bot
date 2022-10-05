use chrono::{DateTime, Local};
use log::{error, info};
use std::env;

use std::{thread, time};

pub mod rte;
pub mod twitter;

use env_logger::Env;

fn main() {
    let env = Env::default().filter_or("LOG_LEVEL", "info");

    env_logger::init_from_env(env);

    let rte_client_id =
        env::var("RTE_CLIENT_ID").expect("env variable `RTE_CLIENT_ID` should be set");
    let rte_client_secret =
        env::var("RTE_CLIENT_SECRET").expect("env variable `RTE_CLIENT_SECRET` should be set");
    let rte_base_url = env::var("RTE_BASE_URL").expect("env variable `RTE_BASE_URL` should be set");

    let twitter_client_id =
        env::var("TWITTER_CLIENT_ID").expect("env variable `TWITTER_CLIENT_ID` should be set");
    let twitter_client_secret = env::var("TWITTER_CLIENT_SECRET")
        .expect("env variable `TWITTER_CLIENT_SECRET` should be set");
    let twitter_token =
        env::var("TWITTER_TOKEN").expect("env variable `TWITTER_TOKEN_ACCESS` should be set");
    let twitter_token_secret = env::var("TWITTER_TOKEN_SECRET")
        .expect("env variable `TWITTER_TOKEN_SECRET` should be set");
    let twitter_url = env::var("TWITTER_URL").expect("env variable `TWITTER_URL` should be set");

    let rte_client = rte::RteClient::new(rte_base_url, rte_client_id, rte_client_secret);

    let twitter_client = twitter::TweetClient::new(
        twitter_url,
        twitter_client_id,
        twitter_client_secret,
        twitter_token,
        twitter_token_secret,
        String::from("templates/tweet.j2"),
    );

    let mut generation_fichier: DateTime<Local> = Local::now();

    info!("starting loop");
    loop {
        match rte_client.fetch_signals() {
            Ok(response) => {
                if response.latest_generation_fichier != generation_fichier {
                    info!(
                        "new version from {}, tweet will be sent",
                        response.latest_generation_fichier
                    );
                    match twitter_client.send_tweet(&response) {
                        Ok(_) => {
                            generation_fichier = response.latest_generation_fichier.clone();
                            info!("tweet sucessfully sent");
                        }
                        Err(e) => error!("failed to post tweet :{:?}", e),
                    }
                } else {
                    info!("no new version, tweet won't be sent")
                }
            }
            Err(e) => {
                error!("failed to retrieve signals {:?}", e);
            }
        };

        thread::sleep(time::Duration::from_secs(15 * 60))
    }
}
