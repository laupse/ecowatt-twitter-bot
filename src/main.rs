use chrono::{DateTime, Local};
use log::{error, info};
use rte::RteClient;
use std::env;
use std::{thread, time};
use twitter::TweetClient;
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
        String::from("templates/prevision_tweet.j2"),
        String::from("templates/daily_prevision_tweet.j2"),
    );

    let mut generation_fichier: DateTime<Local> = Local::now();

    info!("starting loop");
    loop {
        generation_fichier = fetch(&twitter_client, &rte_client, generation_fichier);
        thread::sleep(time::Duration::from_secs(15 * 60))
    }
}

fn fetch(
    twitter_client: &TweetClient,
    rte_client: &RteClient,
    generation_fichier: DateTime<Local>,
) -> DateTime<Local> {
    match rte_client.fetch_signals() {
        Ok(response) => {
            if response.latest_generation_fichier != generation_fichier {
                info!(
                    "new version from {}, tweet will be sent",
                    response.latest_generation_fichier
                );
                match twitter_client.send_tweets(&response) {
                    Ok(_) => info!("tweet sucessfully sent"),

                    // TODO : Make the retweet in the morning
                    // tokio::spawn(async move {
                    //     let duration = Duration::from_millis(100);
                    //     tokio::time::sleep(duration).await;
                    //     let twitter_retweet_client = twitter_client.clone();
                    //     match twitter_retweet_client.clone().retweet_last() {
                    //         Ok(_) => info!("last tweet successfully retweeted"),
                    //         Err(e) => error!("failed to retweet last tweet :{:?}", e),
                    //     }
                    // });
                    Err(e) => error!("failed to post tweet :{:?}", e),
                };
                return response.latest_generation_fichier;
            }
            info!("no new version, tweet won't be sent")
        }
        Err(e) => {
            error!("failed to retrieve signals {:?}", e);
        }
    };
    return generation_fichier;
}
