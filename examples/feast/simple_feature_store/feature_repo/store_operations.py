"""This module contains the operations to execute on the Feast FeatureStore"""

from datetime import datetime

import feast
import pandas as pd

from hamilton.function_modifiers import config


def feature_store(feast_repository_path: str, feast_config: dict) -> feast.FeatureStore:
    """Instantiate Feast core object, the FeatureStore"""
    if feast_config:
        return feast.FeatureStore(repo_path=feast_repository_path, config=feast_config)
    else:
        return feast.FeatureStore(repo_path=feast_repository_path)


def apply(
    feature_store: feast.FeatureStore, feast_objects: list[feast.feast_object.FeastObject]
) -> bool:
    """Register objects to metadata store and update infra; equiv to `feast apply` CLI"""
    feature_store.apply(feast_objects)
    return True


def materialize_incremental(feature_store: feast.FeatureStore, end_date: datetime) -> bool:
    """Loads data from offline store to online store, up to end_date
    Has side-effect only; returns a boolean for lineage
    """
    feature_store.materialize_incremental(end_date=end_date)
    return True


def push(
    feature_store: feast.FeatureStore,
    push_source: str,
    event_df: pd.DataFrame,
    push_mode: feast.data_source.PushMode | int,
) -> bool:
    """Push features to a push source; updates all features associated with this source
    Has side-effect only; returns a boolean for lineage
    """
    if isinstance(push_mode, int):
        push_mode = feast.data_source.PushMode(push_mode)
    feature_store.push(push_source, event_df, to=push_mode)
    return True


@config.when_not(batch_scoring=True)
def historical_features__not_batch(
    feature_store: feast.FeatureStore,
    entity_df: pd.DataFrame,
    historical_features_: list[str] | feast.FeatureService,
) -> pd.DataFrame:
    """Retrieves point-in-time correct historical feature for the specified entities"""
    return feature_store.get_historical_features(
        entity_df=entity_df,
        features=historical_features_,
    ).to_df()


@config.when(batch_scoring=True)
def historical_features__batch(
    feature_store: feast.FeatureStore,
    entity_df: pd.DataFrame,
    entity_timestamp_col: str,
    historical_features_: list[str] | feast.FeatureService,
) -> pd.DataFrame:
    """Retrieves all historical feature for the specified entities
    Setting all timestamp to now() allows to retrieve all rows
    """
    # For batch scoring, we want the latest timestamps
    entity_df[entity_timestamp_col] = pd.to_datetime("now", utc=True)
    return feature_store.get_historical_features(
        entity_df=entity_df,
        features=historical_features_,
    ).to_df()


def online_features(
    feature_store: feast.FeatureStore,
    entity_rows: list[dict],
    online_features_: list[str] | feast.FeatureService | feast.data_source.PushSource,
) -> pd.DataFrame:
    """Fetch online features from a FeatureService source"""
    return feature_store.get_online_features(
        entity_rows=entity_rows,
        features=online_features_,
    ).to_df()
