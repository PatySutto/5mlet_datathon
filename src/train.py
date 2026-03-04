import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import xgboost as xgb
import joblib


def load_data_for_training():
    """
    Carrega dados processados para treinamento.
    
    - Lê o arquivo Excel mais recente da pasta bases/treated
    - Separa features (X) da variável target (y)
    
    Returns:
        tuple: (X, y) - Features e target
    """
    # Caminho para a pasta treated
    treated_path = Path(__file__).parent / 'bases' / 'treated'
    
    # Encontra o arquivo mais recente
    excel_files = list(treated_path.glob('*.xlsx'))
    if not excel_files:
        raise FileNotFoundError(f"Nenhum arquivo encontrado em {treated_path}")
    
    latest_file = max(excel_files, key=lambda x: x.stat().st_mtime)
    print(f"Carregando dados de: {latest_file}")
    
    # Lê o arquivo Excel
    df = pd.read_excel(latest_file)
    
    # Separa features (X) e target (y)
    feature_columns = ['IPV', 'IPS', 'IAN', 'IEG', 'INDE', 'IAA', 'IDA']
    X = df[feature_columns]
    y = df['PEDRA']
    
    print(f"Dados carregados: {len(df)} registros")
    print(f"Features: {feature_columns}")
    print(f"Classes: {y.unique().tolist()}")
    print(f"Distribuição de classes:\n{y.value_counts()}")
    
    return X, y


def train_model(X, y, test_size=0.2, random_state=42):
    """
    Treina um modelo XGBoost para classificação de pedras.
    
    Args:
        X (pd.DataFrame): Features
        y (pd.Series): Target (PEDRA)
        test_size (float): Proporção do test set
        random_state (int): Seed para reprodutibilidade
    
    Returns:
        tuple: (model, encoder, X_test, y_test)
    """
    print("\n" + "=" * 50)
    print("Iniciando treinamento do modelo")
    print("=" * 50)
    
    # Codifica as labels para valores numéricos
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    print(f"\nClasses codificadas:")
    for i, class_name in enumerate(label_encoder.classes_):
        print(f"  {class_name} -> {i}")
    
    # Split train/test com estratificação
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, 
        test_size=test_size, 
        random_state=random_state,
        stratify=y_encoded
    )
    
    print(f"\nDivisão dos dados:")
    print(f"  Treino: {len(X_train)} registros")
    print(f"  Teste: {len(X_test)} registros")
    
    # Inicializa o modelo XGBoost
    model = xgb.XGBClassifier(
        max_depth=6,
        n_estimators=100,
        learning_rate=0.1,
        random_state=random_state,
        eval_metric='mlogloss',
        use_label_encoder=False
    )
    
    # Treina o modelo
    print("\nTreinando modelo XGBoost...")
    model.fit(X_train, y_train)
    print("Treinamento concluído!")
    
    return model, label_encoder, X_test, y_test


def evaluate_model(model, label_encoder, X_test, y_test):
    """
    Avalia o modelo treinado no conjunto de teste.
    
    Args:
        model: Modelo treinado
        label_encoder: LabelEncoder usado no treinamento
        X_test: Features de teste
        y_test: Labels de teste (codificadas)
    
    Returns:
        dict: Dicionário com métricas de avaliação
    """
    print("\n" + "=" * 50)
    print("Avaliação do Modelo")
    print("=" * 50)
    
    # Faz predições
    y_pred = model.predict(X_test)
    
    # Calcula acurácia
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nAcurácia: {accuracy:.4f} ({accuracy*100:.2f}%)")
    
    # Relatório de classificação
    print("\nRelatório de Classificação:")
    print(classification_report(
        y_test, 
        y_pred, 
        target_names=label_encoder.classes_
    ))
    
    # Matriz de confusão
    print("Matriz de Confusão:")
    cm = confusion_matrix(y_test, y_pred)
    print(cm)
    
    # Retorna métricas
    metrics = {
        'accuracy': accuracy,
        'confusion_matrix': cm,
        'classification_report': classification_report(
            y_test, y_pred, target_names=label_encoder.classes_, output_dict=True
        )
    }
    
    return metrics


def save_model_artifacts(model, label_encoder, feature_names):
    """
    Salva o modelo treinado e o label encoder.
    
    Args:
        model: Modelo XGBoost treinado
        label_encoder: LabelEncoder usado no treinamento
        feature_names: Lista de nomes das features
    """
    # Cria diretório de modelos
    models_path = Path(__file__).parent.parent / 'app' / 'modelo'
    models_path.mkdir(parents=True, exist_ok=True)
    
    # Data de criação para o nome do arquivo
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Salva o modelo XGBoost como .joblib
    model_file = models_path / f'xgboost_pedra_classifier_{today}.joblib'
    joblib.dump(model, model_file)
    print(f"\nModelo salvo em: {model_file}")
    
    # Salva o label encoder
    encoder_file = models_path / f'label_encoder_{today}.pkl'
    joblib.dump(label_encoder, encoder_file)
    print(f"Label Encoder salvo em: {encoder_file}")
    
    # Salva os nomes das features
    features_file = models_path / f'feature_names_{today}.pkl'
    joblib.dump(feature_names, features_file)
    print(f"Feature names salvos em: {features_file}")
    
    print("\nTodos os artefatos salvos com sucesso!")


def print_feature_importance(model, feature_names):
    """
    Imprime a importância de cada feature no modelo.
    
    Args:
        model: Modelo treinado
        feature_names: Lista de nomes das features
    """
    print("\n" + "=" * 50)
    print("Importância das Features")
    print("=" * 50)
    
    # Obtém importâncias
    importances = model.feature_importances_
    
    # Cria DataFrame para ordenação
    feature_importance_df = pd.DataFrame({
        'Feature': feature_names,
        'Importance': importances
    }).sort_values('Importance', ascending=False)
    
    print("\n" + feature_importance_df.to_string(index=False))


if __name__ == '__main__':
    print("=" * 50)
    print("TREINAMENTO DO MODELO XGBOOST")
    print("Classificação de Tipos de Pedra")
    print("=" * 50)
    
    # 1. Carrega dados
    X, y = load_data_for_training()
    
    # 2. Treina o modelo
    model, encoder, X_test, y_test = train_model(X, y)
    
    # 3. Avalia o modelo
    metrics = evaluate_model(model, encoder, X_test, y_test)
    
    # 4. Mostra importância das features
    print_feature_importance(model, X.columns.tolist())
    
    # 5. Salva o modelo e artefatos
    save_model_artifacts(model, encoder, X.columns.tolist())
    
    print("\n" + "=" * 50)
    print("TREINAMENTO CONCLUÍDO!")
    print("=" * 50)
