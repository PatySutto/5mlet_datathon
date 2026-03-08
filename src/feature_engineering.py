import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from feast import Entity, FeatureStore, FeatureView, Field, FileSource, ValueType
from feast.types import String, Float64, Int64


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
    
    # Verifica e adiciona student_id se não existir
    if 'student_id' not in df.columns:
        print("⚠️  student_id não encontrado, adicionando...")
        df.insert(0, 'student_id', range(len(df)))
    else:
        print("✅ student_id column verified")
    
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
    # Define a entidade student (cada linha = um estudante)
    student_entity = Entity(
        name="student",
        join_keys=["student_id"],
        value_type=ValueType.INT64,
        description="Identificador único do estudante"
    )
    
    # Define a fonte de dados (arquivo parquet)
    features_path = Path(__file__).parent / 'bases' / 'features' / 'pedras_features.parquet'
    
    pedras_source = FileSource(
        path=str(features_path),
        timestamp_field="event_timestamp"
    )
    
    # Define a Feature View com todas as features numéricas
    student_features_fv = FeatureView(
        name="student_features",
        entities=[student_entity],
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
    
    return student_entity, student_features_fv


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


def get_features(student_ids, store=None):
    """
    Recupera features para IDs específicos de estudantes.
    
    Args:
        student_ids (list): Lista de IDs de estudantes
        store (FeatureStore, optional): Instância do FeatureStore
    
    Returns:
        pd.DataFrame: DataFrame com as features recuperadas
    """
    if store is None:
        repo_path = Path(__file__).parent
        store = FeatureStore(repo_path=str(repo_path))
    
    # Cria DataFrame com as entidades
    entity_df = pd.DataFrame({
        "student_id": student_ids,
        "event_timestamp": [pd.Timestamp.now()] * len(student_ids)
    })
    
    # Recupera as features
    features = store.get_historical_features(
        entity_df=entity_df,
        features=[
            "student_features:IPV",
            "student_features:IPS",
            "student_features:IAN",
            "student_features:IEG",
            "student_features:INDE",
            "student_features:IAA",
            "student_features:IDA",
        ]
    ).to_df()
    
    return features


def get_features_for_training(store=None):
    """
    Carrega dados de treinamento completo do Feast Feature Store.
    Retorna X (features) e y (target) no mesmo formato que load_data_for_training().
    
    Args:
        store (FeatureStore, optional): Instância do FeatureStore
    
    Returns:
        tuple: (X, y) - Features DataFrame e target Series
    """
    # Verifica se o arquivo parquet existe
    features_path = Path(__file__).parent / 'bases' / 'features' / 'pedras_features.parquet'
    
    if not features_path.exists():
        raise FileNotFoundError(
            f"Arquivo de features não encontrado: {features_path}\n"
            "Execute prepare_feature_data() primeiro."
        )
    
    # Lê o parquet para obter todos os student_ids e PEDRA (target)
    df_base = pd.read_parquet(features_path)
    
    if 'student_id' not in df_base.columns:
        raise ValueError(
            "Coluna 'student_id' não encontrada no arquivo de features.\n"
            "Execute o preprocessing com a versão atualizada que adiciona student_id."
        )
    
    student_ids = df_base['student_id'].tolist()
    event_timestamps = df_base['event_timestamp'].tolist()
    
    print(f"Carregando {len(student_ids)} registros do Feast Feature Store...")
    
    # Inicializa Feature Store se não fornecido
    if store is None:
        repo_path = Path(__file__).parent
        store = FeatureStore(repo_path=str(repo_path))
    
    # Cria entity DataFrame
    entity_df = pd.DataFrame({
        "student_id": student_ids,
        "event_timestamp": event_timestamps
    })
    
    # Recupera features do Feast
    features_df = store.get_historical_features(
        entity_df=entity_df,
        features=[
            "student_features:IPV",
            "student_features:IPS",
            "student_features:IAN",
            "student_features:IEG",
            "student_features:INDE",
            "student_features:IAA",
            "student_features:IDA",
        ]
    ).to_df()
    
    # Merge com PEDRA (target) do parquet original
    # PEDRA não é armazenado no Feast pois é o target, não uma feature
    features_df = features_df.merge(
        df_base[['student_id', 'PEDRA']], 
        on='student_id', 
        how='left'
    )
    
    # Separa X (features) e y (target)
    feature_columns = ['IPV', 'IPS', 'IAN', 'IEG', 'INDE', 'IAA', 'IDA']
    X = features_df[feature_columns]
    y = features_df['PEDRA']
    
    print(f"Dados carregados via Feast: {len(X)} registros")
    print(f"Features: {feature_columns}")
    print(f"Classes: {y.unique().tolist()}")
    print(f"Distribuição de classes:\n{y.value_counts()}")
    
    return X, y


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
    
    # 3. Exemplo: recupera features para alguns estudantes
    print("\n3. Testando recuperação de features...")
    student_ids_exemplo = df['student_id'].head(3).tolist()
    print(f"   - Recuperando features para student_ids: {student_ids_exemplo}")
    
    features_df = get_features(student_ids_exemplo, store)
    print("\nFeatures recuperadas:")
    print(features_df)
    
    # 4. Testa carregamento completo para treinamento
    print("\n4. Testando carregamento completo para treinamento...")
    X, y = get_features_for_training(store)
    print(f"   - X shape: {X.shape}")
    print(f"   - y shape: {y.shape}")
    print(f"   - Primeiras 3 linhas de X:\n{X.head(3)}")
    print(f"   - Primeiras 3 linhas de y:\n{y.head(3)}")
    
    print("\n" + "=" * 50)
    print("Concluído!")
    print("=" * 50)
