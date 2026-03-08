import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import mlflow
import mlflow.xgboost
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, 
    precision_score, 
    recall_score, 
    f1_score,
    classification_report, 
    confusion_matrix
)
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import re


def sanitize_metric_name(name):
    """
    Sanitiza o nome de uma métrica para ser compatível com MLflow.
    MLflow permite apenas: alphanumerics, underscores (_), dashes (-), 
    periods (.), spaces ( ), colon(:) e slashes (/).
    
    Args:
        name (str): Nome original da classe/métrica
        
    Returns:
        str: Nome sanitizado compatível com MLflow
        
    Examples:
        >>> sanitize_metric_name("#NULO!")
        'NULO'
        >>> sanitize_metric_name("Class@123")
        'Class_123'
    """
    # Define os caracteres permitidos pelo MLflow
    # Mantém apenas: alphanumerics, _, -, ., espaço, :, /
    sanitized = re.sub(r'[^a-zA-Z0-9_\-.: /]', '_', str(name))
    # Remove underscores duplicados
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove underscores do início e fim
    sanitized = sanitized.strip('_')
    return sanitized


def load_latest_model():
    """
    Carrega o modelo mais recente da pasta app/modelo.
    
    Returns:
        tuple: (model, label_encoder, feature_names)
    """
    models_path = Path(__file__).parent.parent / 'app' / 'modelo'
    
    # Encontra os arquivos mais recentes
    model_files = list(models_path.glob('xgboost_pedra_classifier_*.joblib'))
    encoder_files = list(models_path.glob('label_encoder_*.pkl'))
    features_files = list(models_path.glob('feature_names_*.pkl'))
    
    if not model_files or not encoder_files or not features_files:
        raise FileNotFoundError(f"Arquivos do modelo não encontrados em {models_path}")
    
    # Pega os mais recentes
    latest_model = max(model_files, key=lambda x: x.stat().st_mtime)
    latest_encoder = max(encoder_files, key=lambda x: x.stat().st_mtime)
    latest_features = max(features_files, key=lambda x: x.stat().st_mtime)
    
    print(f"Carregando modelo de: {latest_model}")
    print(f"Carregando encoder de: {latest_encoder}")
    print(f"Carregando features de: {latest_features}")
    
    # Carrega os artefatos
    model = joblib.load(latest_model)
    label_encoder = joblib.load(latest_encoder)
    feature_names = joblib.load(latest_features)
    
    return model, label_encoder, feature_names


def load_test_data():
    """
    Carrega dados de teste para avaliação.
    
    Returns:
        tuple: (X_test, y_test, y_test_encoded)
    """
    # Caminho para a pasta treated
    treated_path = Path(__file__).parent / 'bases' / 'treated'
    
    # Encontra o arquivo mais recente
    excel_files = list(treated_path.glob('*.xlsx'))
    if not excel_files:
        raise FileNotFoundError(f"Nenhum arquivo encontrado em {treated_path}")
    
    latest_file = max(excel_files, key=lambda x: x.stat().st_mtime)
    print(f"\nCarregando dados de: {latest_file}")
    
    # Lê o arquivo Excel
    df = pd.read_excel(latest_file)
    
    # Separa features (X) e target (y)
    feature_columns = ['IPV', 'IPS', 'IAN', 'IEG', 'INDE', 'IAA', 'IDA']
    X = df[feature_columns]
    y = df['PEDRA']
    
    # Codifica as labels (mesma codificação do treinamento)
    from sklearn.preprocessing import LabelEncoder
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    # Split train/test (mesmo split do treinamento)
    _, X_test, _, y_test = train_test_split(
        X, y_encoded, 
        test_size=0.2, 
        random_state=42,
        stratify=y_encoded
    )
    
    print(f"Dados de teste: {len(X_test)} registros")
    
    return X_test, y_test, y


def plot_confusion_matrix(y_true, y_pred, class_names, output_path):
    """
    Cria e salva um gráfico da matriz de confusão.
    
    Args:
        y_true: Labels verdadeiras
        y_pred: Predições do modelo
        class_names: Nomes das classes
        output_path: Caminho para salvar o gráfico
    """
    cm = confusion_matrix(y_true, y_pred)
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        cm, 
        annot=True, 
        fmt='d', 
        cmap='Blues',
        xticklabels=class_names,
        yticklabels=class_names
    )
    plt.title('Matriz de Confusão')
    plt.ylabel('Verdadeiro')
    plt.xlabel('Predito')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Matriz de confusão salva em: {output_path}")


def plot_feature_importance(model, feature_names, output_path):
    """
    Cria e salva um gráfico de importância das features.
    
    Args:
        model: Modelo treinado
        feature_names: Lista de nomes das features
        output_path: Caminho para salvar o gráfico
    """
    importances = model.feature_importances_
    
    # Cria DataFrame para ordenação
    feature_importance_df = pd.DataFrame({
        'Feature': feature_names,
        'Importance': importances
    }).sort_values('Importance', ascending=True)
    
    plt.figure(figsize=(10, 6))
    plt.barh(feature_importance_df['Feature'], feature_importance_df['Importance'])
    plt.xlabel('Importância')
    plt.title('Importância das Features')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Importância das features salva em: {output_path}")


def evaluate_with_mlflow(model, label_encoder, feature_names, X_test, y_test):
    """
    Avalia o modelo e registra tudo no MLFlow.
    
    Args:
        model: Modelo treinado
        label_encoder: LabelEncoder usado no treinamento
        feature_names: Lista de nomes das features
        X_test: Features de teste
        y_test: Labels de teste (codificadas)
    
    Returns:
        dict: Dicionário com métricas de avaliação
    """
    # Configura MLFlow com caminho absoluto
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    mlruns_path = project_root / "mlruns"
    mlflow.set_tracking_uri(f"file:{mlruns_path}")
    mlflow.set_experiment("pedras_classification")
    
    # Habilita auto-logging do XGBoost
    mlflow.xgboost.autolog()
    
    # Inicia um run do MLFlow
    with mlflow.start_run(run_name=f"evaluation_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"):
        
        print("\n" + "=" * 50)
        print("AVALIAÇÃO COM MLFLOW")
        print("=" * 50)
        
        # Log dos parâmetros do modelo
        mlflow.log_param("model_type", "XGBoost")
        mlflow.log_param("max_depth", model.max_depth)
        mlflow.log_param("n_estimators", model.n_estimators)
        mlflow.log_param("learning_rate", model.learning_rate)
        mlflow.log_param("n_features", len(feature_names))
        mlflow.log_param("n_classes", len(label_encoder.classes_))
        mlflow.log_param("test_size", len(X_test))
        
        # Faz predições
        y_pred = model.predict(X_test)
        
        # Calcula métricas
        accuracy = accuracy_score(y_test, y_pred)
        precision_macro = precision_score(y_test, y_pred, average='macro', zero_division=0)
        recall_macro = recall_score(y_test, y_pred, average='macro', zero_division=0)
        f1_macro = f1_score(y_test, y_pred, average='macro', zero_division=0)
        
        precision_weighted = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        recall_weighted = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1_weighted = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        
        # Log das métricas principais
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("precision_macro", precision_macro)
        mlflow.log_metric("recall_macro", recall_macro)
        mlflow.log_metric("f1_macro", f1_macro)
        mlflow.log_metric("precision_weighted", precision_weighted)
        mlflow.log_metric("recall_weighted", recall_weighted)
        mlflow.log_metric("f1_weighted", f1_weighted)
        
        print(f"\nMétricas Principais:")
        print(f"  Accuracy:          {accuracy:.4f} ({accuracy*100:.2f}%)")
        print(f"  Precision (macro): {precision_macro:.4f}")
        print(f"  Recall (macro):    {recall_macro:.4f}")
        print(f"  F1-Score (macro):  {f1_macro:.4f}")
        
        # Log de métricas por classe
        print(f"\nMétricas por Classe:")
        precision_per_class = precision_score(y_test, y_pred, average=None, zero_division=0)
        recall_per_class = recall_score(y_test, y_pred, average=None, zero_division=0)
        f1_per_class = f1_score(y_test, y_pred, average=None, zero_division=0)
        
        # Construir dicionário de métricas por classe
        per_class_metrics = {}
        for i, class_name in enumerate(label_encoder.classes_):
            # Sanitiza o nome da classe para uso em métricas do MLflow
            sanitized_name = sanitize_metric_name(class_name)
            mlflow.log_metric(f"precision_{sanitized_name}", precision_per_class[i])
            mlflow.log_metric(f"recall_{sanitized_name}", recall_per_class[i])
            mlflow.log_metric(f"f1_{sanitized_name}", f1_per_class[i])
            print(f"  {class_name}: P={precision_per_class[i]:.3f}, R={recall_per_class[i]:.3f}, F1={f1_per_class[i]:.3f}")
            
            # Usa o nome original da classe no dicionário de métricas (para API)
            per_class_metrics[class_name] = {
                'precision': float(precision_per_class[i]),
                'recall': float(recall_per_class[i]),
                'f1-score': float(f1_per_class[i]),
                'support': int(np.sum(y_test == i))
            }
        
        # Cria pasta temporária para artefatos
        artifacts_path = Path(__file__).parent.parent / 'mlflow_artifacts'
        artifacts_path.mkdir(exist_ok=True)
        
        # Plota e salva matriz de confusão
        cm_path = artifacts_path / 'confusion_matrix.png'
        plot_confusion_matrix(y_test, y_pred, label_encoder.classes_, cm_path)
        mlflow.log_artifact(str(cm_path))
        
        # Plota e salva importância das features
        fi_path = artifacts_path / 'feature_importance.png'
        plot_feature_importance(model, feature_names, fi_path)
        mlflow.log_artifact(str(fi_path))
        
        # Salva relatório de classificação
        report = classification_report(y_test, y_pred, target_names=label_encoder.classes_)
        report_path = artifacts_path / 'classification_report.txt'
        with open(report_path, 'w') as f:
            f.write(report)
        mlflow.log_artifact(str(report_path))
        
        print(f"\nRelatório de Classificação:")
        print(report)
        
        # Log do modelo
        mlflow.xgboost.log_model(model, "model")
        
        # Log de tags
        mlflow.set_tag("model_version", datetime.now().strftime('%Y-%m-%d'))
        mlflow.set_tag("dataset", "pedras")
        
        # Pega o run_id
        run_id = mlflow.active_run().info.run_id
        print(f"\nMLFlow Run ID: {run_id}")
        
        # Retorna métricas
        metrics = {
            'accuracy': accuracy,
            'precision_macro': precision_macro,
            'recall_macro': recall_macro,
            'f1_macro': f1_macro,
            'precision_weighted': precision_weighted,
            'recall_weighted': recall_weighted,
            'f1_weighted': f1_weighted,
            'per_class_metrics': per_class_metrics,
            'run_id': run_id
        }
        
        return metrics


if __name__ == '__main__':
    print("=" * 50)
    print("AVALIAÇÃO DO MODELO COM MLFLOW")
    print("=" * 50)
    
    # 1. Carrega o modelo mais recente
    print("\n1. Carregando modelo...")
    model, label_encoder, feature_names = load_latest_model()
    print(f"   - Modelo carregado com sucesso")
    print(f"   - Classes: {label_encoder.classes_.tolist()}")
    print(f"   - Features: {feature_names}")
    
    # 2. Carrega dados de teste
    print("\n2. Carregando dados de teste...")
    X_test, y_test, y_original = load_test_data()
    
    # 3. Avalia com MLFlow
    print("\n3. Avaliando modelo com MLFlow...")
    metrics = evaluate_with_mlflow(model, label_encoder, feature_names, X_test, y_test)
    
    print("\n" + "=" * 50)
    print("AVALIAÇÃO CONCLUÍDA!")
    print("=" * 50)
    print(f"\nRun ID: {metrics['run_id']}")
    print("\nPara visualizar os resultados no MLFlow UI:")
    print("  mlflow ui")
    print("  Acesse: http://localhost:5000")
    print("\n" + "=" * 50)
