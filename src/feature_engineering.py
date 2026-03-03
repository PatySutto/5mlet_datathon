import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from feast import Entity, FeatureStore, FeatureView, Field, FileSource
from feast.types import String, Float64


def prepare_feature_data():
    """
    Prepara os dados dos arquivos tratados para o Feast.
    
    - Lê o arquivo Excel mais recente da pasta bases/treated
    - Adiciona coluna event_timestamp necessária para o Feast
    - Salva como parquet em bases/features
    
    Returns:
        pd.DataFrame: DataFrame preparado para features
    """
    # Caminho para a pasta treated
    treated_path = Path(__file__).parent / 'bases' / 'treated'
    
    # Encontra o arquivo mais recente
    excel_files = list(treated_path.glob('*.xlsx'))
    if not excel_files:
        raise FileNotFoundError(f"Nenhum arquivo encontrado em {treated_path}")
    
    latest_file = max(excel_files, key=lambda x: x.stat().st_mtime)
    print(f"Lendo arquivo: {latest_file}")
    
    # Lê o arquivo Excel
    df = pd.read_excel(latest_file)
    
    # Adiciona timestamp para o Feast (usa timestamp atual)
    df['event_timestamp'] = pd.Timestamp.now()
    
    # Cria pasta features se não existir
    features_path = Path(__file__).parent / 'bases' / 'features'
    features_path.mkdir(parents=True, exist_ok=True)
    
    # Salva como parquet
    output_file = features_path / 'pedras_features.parquet'
    df.to_parquet(output_file, index=False)
    print(f"Dados salvos em: {output_file}")
    
    return df


def define_feature_components():
    """
    Define os componentes do Feast: Entity, FileSource e FeatureView.
    
    Returns:
        tuple: (entity, feature_view)
    """
    # Define a entidade PEDRA
    pedra_entity = Entity(
        name="pedra",
        join_keys=["PEDRA"],
        description="Identificador único da pedra"
    )
    
    # Define a fonte de dados (arquivo parquet)
    features_path = Path(__file__).parent / 'bases' / 'features' / 'pedras_features.parquet'
    
    pedras_source = FileSource(
        path=str(features_path),
        timestamp_field="event_timestamp"
    )
    
    # Define a Feature View com todas as features numéricas
    pedras_fv = FeatureView(
        name="pedras_features",
        entities=[pedra_entity],
        ttl=timedelta(days=30),
        schema=[
            Field(name="IPV", dtype=Float64),
            Field(name="IPS", dtype=Float64),
            Field(name="IAN", dtype=Float64),
            Field(name="IEG", dtype=Float64),
            Field(name="INDE", dtype=Float64),
            Field(name="IAA", dtype=Float64),
            Field(name="IDA", dtype=Float64),
        ],
        source=pedras_source,
        online=False,
    )
    
    return pedra_entity, pedras_fv


def initialize_feature_store():
    """
    Inicializa o Feature Store do Feast.
    
    - Aplica as definições de entity e feature views
    - Retorna a instância do FeatureStore
    
    Returns:
        FeatureStore: Instância configurada do Feast
    """
    # Caminho do repositório (pasta src/)
    repo_path = Path(__file__).parent
    
    # Inicializa o FeatureStore
    store = FeatureStore(repo_path=str(repo_path))
    
    # Define os componentes
    entity, feature_view = define_feature_components()
    
    # Aplica as definições
    print("Aplicando definições ao Feature Store...")
    store.apply([entity, feature_view])
    print("Feature Store inicializado com sucesso!")
    
    return store


def get_features(pedra_values, store=None):
    """
    Recupera features para valores específicos de PEDRA.
    
    Args:
        pedra_values (list): Lista de valores de PEDRA
        store (FeatureStore, optional): Instância do FeatureStore
    
    Returns:
        pd.DataFrame: DataFrame com as features recuperadas
    """
    if store is None:
        repo_path = Path(__file__).parent
        store = FeatureStore(repo_path=str(repo_path))
    
    # Cria DataFrame com as entidades
    entity_df = pd.DataFrame({
        "PEDRA": pedra_values,
        "event_timestamp": [pd.Timestamp.now()] * len(pedra_values)
    })
    
    # Recupera as features
    features = store.get_historical_features(
        entity_df=entity_df,
        features=[
            "pedras_features:IPV",
            "pedras_features:IPS",
            "pedras_features:IAN",
            "pedras_features:IEG",
            "pedras_features:INDE",
            "pedras_features:IAA",
            "pedras_features:IDA",
        ]
    ).to_df()
    
    return features


if __name__ == '__main__':
    print("=" * 50)
    print("Feature Engineering com Feast")
    print("=" * 50)
    
    # 1. Prepara os dados
    print("\n1. Preparando dados...")
    df = prepare_feature_data()
    print(f"   - {len(df)} registros carregados")
    print(f"   - Colunas: {df.columns.tolist()}")
    
    # 2. Inicializa o Feature Store
    print("\n2. Inicializando Feature Store...")
    store = initialize_feature_store()
    
    # 3. Exemplo: recupera features para algumas pedras
    print("\n3. Testando recuperação de features...")
    pedras_exemplo = df['PEDRA'].unique()[:3].tolist()
    print(f"   - Recuperando features para: {pedras_exemplo}")
    
    features_df = get_features(pedras_exemplo, store)
    print("\nFeatures recuperadas:")
    print(features_df)
    
    print("\n" + "=" * 50)
    print("Concluído!")
    print("=" * 50)
