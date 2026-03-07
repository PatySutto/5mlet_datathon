"""Script de treinamento do modelo XGBoost com parâmetros configuráveis.

Exemplos de uso:
    # Treino com parâmetros padrão
    python src/train.py
    
    # Treino com parâmetros customizados
    python src/train.py --max-depth 8 --n-estimators 200 --learning-rate 0.05
    
    # Teste rápido sem salvar
    python src/train.py --max-depth 4 --no-save
    
    # Grid search para encontrar melhores parâmetros
    python src/train.py --grid-search --max-depth-range "4,6,8" --n-estimators-range "50,100,200"
"""

import pandas as pd
import numpy as np
import argparse
import sys
from pathlib import Path
from datetime import datetime
from itertools import product
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


def train_model(X, y, max_depth=6, n_estimators=100, learning_rate=0.1, 
                test_size=0.2, random_state=42, verbose=True):
    """
    Treina um modelo XGBoost para classificação de pedras.
    
    Args:
        X (pd.DataFrame): Features
        y (pd.Series): Target (PEDRA)
        max_depth (int): Profundidade máxima das árvores
        n_estimators (int): Número de árvores (boosting rounds)
        learning_rate (float): Taxa de aprendizado
        test_size (float): Proporção do test set
        random_state (int): Seed para reprodutibilidade
        verbose (bool): Se True, imprime informações detalhadas
    
    Returns:
        tuple: (model, encoder, X_test, y_test, X_train, y_train)
    """
    if verbose:
        print("\n" + "=" * 50)
        print("Iniciando treinamento do modelo")
        print("=" * 50)
        print("\n📊 Parâmetros do modelo:")
        print(f"  max_depth: {max_depth}")
        print(f"  n_estimators: {n_estimators}")
        print(f"  learning_rate: {learning_rate}")
        print(f"  test_size: {test_size}")
        print(f"  random_state: {random_state}")
    
    # Codifica as labels para valores numéricos
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    if verbose:
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
    
    if verbose:
        print(f"\nDivisão dos dados:")
        print(f"  Treino: {len(X_train)} registros")
        print(f"  Teste: {len(X_test)} registros")
    
    # Inicializa o modelo XGBoost com parâmetros configuráveis
    model = xgb.XGBClassifier(
        max_depth=max_depth,
        n_estimators=n_estimators,
        learning_rate=learning_rate,
        random_state=random_state,
        eval_metric='mlogloss',
        use_label_encoder=False
    )
    
    # Treina o modelo
    if verbose:
        print("\nTreinando modelo XGBoost...")
    model.fit(X_train, y_train, verbose=False)
    if verbose:
        print("Treinamento concluído!")
    
    return model, label_encoder, X_test, y_test, X_train, y_train


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


def save_model_artifacts(model, label_encoder, feature_names, save_enabled=True, suffix=''):
    """
    Salva o modelo treinado e o label encoder.
    
    Args:
        model: Modelo XGBoost treinado
        label_encoder: LabelEncoder usado no treinamento
        feature_names: Lista de nomes das features
        save_enabled (bool): Se False, não salva os artefatos
        suffix (str): Sufixo adicional para o nome dos arquivos (ex: '_gridsearch')
    """
    if not save_enabled:
        print("\n⚠️  Modelo não salvo (flag --no-save ativada)")
        return
    
    # Cria diretório de modelos
    models_path = Path(__file__).parent.parent / 'app' / 'modelo'
    models_path.mkdir(parents=True, exist_ok=True)
    
    # Data de criação para o nome do arquivo
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Salva o modelo XGBoost como .joblib
    model_file = models_path / f'xgboost_pedra_classifier_{today}{suffix}.joblib'
    joblib.dump(model, model_file)
    print(f"\n💾 Modelo salvo em: {model_file}")
    
    # Salva o label encoder
    encoder_file = models_path / f'label_encoder_{today}{suffix}.pkl'
    joblib.dump(label_encoder, encoder_file)
    print(f"💾 Label Encoder salvo em: {encoder_file}")
    
    # Salva os nomes das features
    features_file = models_path / f'feature_names_{today}{suffix}.pkl'
    joblib.dump(feature_names, features_file)
    print(f"💾 Feature names salvos em: {features_file}")
    
    print("\n✅ Todos os artefatos salvos com sucesso!")


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


def parse_arguments():
    """
    Parseia argumentos da linha de comando.
    
    Returns:
        argparse.Namespace: Argumentos parseados
    """
    parser = argparse.ArgumentParser(
        description='Treinar modelo XGBoost para classificação de pedras',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  # Treino com parâmetros padrão
  python src/train.py
  
  # Treino com parâmetros customizados
  python src/train.py --max-depth 8 --n-estimators 200 --learning-rate 0.05
  
  # Teste rápido sem salvar modelo
  python src/train.py --max-depth 4 --no-save
  
  # Grid search simples
  python src/train.py --grid-search --max-depth-range "4,6,8" --n-estimators-range "50,100"
  
  # Grid search completo
  python src/train.py --grid-search --max-depth-range "4,6,8" \
                      --n-estimators-range "50,100,200" \
                      --learning-rate-range "0.05,0.1,0.2"
        """
    )
    
    # Parâmetros do modelo XGBoost
    model_group = parser.add_argument_group('Parâmetros do Modelo XGBoost')
    model_group.add_argument(
        '--max-depth',
        type=int,
        default=6,
        help='Profundidade máxima das árvores (padrão: 6, range: 3-10)'
    )
    model_group.add_argument(
        '--n-estimators',
        type=int,
        default=100,
        help='Número de árvores/boosting rounds (padrão: 100, range: 50-500)'
    )
    model_group.add_argument(
        '--learning-rate',
        type=float,
        default=0.1,
        help='Taxa de aprendizado (padrão: 0.1, range: 0.01-0.3)'
    )
    
    # Parâmetros de treinamento
    train_group = parser.add_argument_group('Parâmetros de Treinamento')
    train_group.add_argument(
        '--test-size',
        type=float,
        default=0.2,
        help='Proporção dos dados para teste (padrão: 0.2, range: 0.1-0.3)'
    )
    train_group.add_argument(
        '--random-state',
        type=int,
        default=42,
        help='Seed para reprodutibilidade (padrão: 42)'
    )
    
    # Opções de execução
    exec_group = parser.add_argument_group('Opções de Execução')
    exec_group.add_argument(
        '--no-save',
        action='store_true',
        help='Não salvar o modelo treinado (útil para testes rápidos)'
    )
    exec_group.add_argument(
        '--grid-search',
        action='store_true',
        help='Ativar busca em grade para encontrar melhores hiperparâmetros'
    )
    
    # Parâmetros para grid search
    grid_group = parser.add_argument_group('Parâmetros de Grid Search')
    grid_group.add_argument(
        '--max-depth-range',
        type=str,
        help='Range de max_depth para grid search (ex: "4,6,8")'
    )
    grid_group.add_argument(
        '--n-estimators-range',
        type=str,
        help='Range de n_estimators para grid search (ex: "50,100,200")'
    )
    grid_group.add_argument(
        '--learning-rate-range',
        type=str,
        help='Range de learning_rate para grid search (ex: "0.05,0.1,0.2")'
    )
    
    return parser.parse_args()


def validate_arguments(args):
    """
    Valida os argumentos fornecidos.
    
    Args:
        args: Argumentos parseados
        
    Returns:
        bool: True se válido, False caso contrário
    """
    errors = []
    
    # Validar max_depth
    if args.max_depth < 3 or args.max_depth > 10:
        errors.append(f"--max-depth deve estar entre 3 e 10 (fornecido: {args.max_depth})")
    
    # Validar n_estimators
    if args.n_estimators < 50 or args.n_estimators > 500:
        errors.append(f"--n-estimators deve estar entre 50 e 500 (fornecido: {args.n_estimators})")
    
    # Validar learning_rate
    if args.learning_rate < 0.01 or args.learning_rate > 0.3:
        errors.append(f"--learning-rate deve estar entre 0.01 e 0.3 (fornecido: {args.learning_rate})")
    
    # Validar test_size
    if args.test_size < 0.1 or args.test_size > 0.3:
        errors.append(f"--test-size deve estar entre 0.1 e 0.3 (fornecido: {args.test_size})")
    
    # Validar grid search
    if args.grid_search:
        if not any([args.max_depth_range, args.n_estimators_range, args.learning_rate_range]):
            errors.append("Para usar --grid-search, forneça pelo menos um range de parâmetros")
    
    if errors:
        print("❌ Erros de validação:")
        for error in errors:
            print(f"   {error}")
        return False
    
    return True


def parse_range(range_str, param_type=int):
    """
    Converte string de range em lista de valores.
    
    Args:
        range_str (str): String com valores separados por vírgula
        param_type (type): Tipo dos valores (int ou float)
        
    Returns:
        list: Lista de valores
    """
    if not range_str:
        return None
    
    try:
        values = [param_type(v.strip()) for v in range_str.split(',')]
        return values
    except ValueError as e:
        print(f"❌ Erro ao parsear range '{range_str}': {e}")
        return None


def run_grid_search(X, y, max_depth_range=None, n_estimators_range=None, 
                    learning_rate_range=None, test_size=0.2, random_state=42):
    """
    Executa busca em grade para encontrar melhores hiperparâmetros.
    
    Args:
        X (pd.DataFrame): Features
        y (pd.Series): Target
        max_depth_range (list): Lista de valores de max_depth para testar
        n_estimators_range (list): Lista de valores de n_estimators para testar
        learning_rate_range (list): Lista de valores de learning_rate para testar
        test_size (float): Proporção do test set
        random_state (int): Seed para reprodutibilidade
        
    Returns:
        tuple: (best_model, best_encoder, best_params, all_results)
    """
    # Usar valores padrão se range não fornecido
    max_depth_range = max_depth_range or [6]
    n_estimators_range = n_estimators_range or [100]
    learning_rate_range = learning_rate_range or [0.1]
    
    # Gerar todas as combinações
    param_combinations = list(product(max_depth_range, n_estimators_range, learning_rate_range))
    
    print("\n" + "=" * 70)
    print("🔍 GRID SEARCH - Busca de Hiperparâmetros")
    print("=" * 70)
    print(f"\nTestando {len(param_combinations)} combinações de parâmetros:")
    print(f"  max_depth: {max_depth_range}")
    print(f"  n_estimators: {n_estimators_range}")
    print(f"  learning_rate: {learning_rate_range}")
    
    if len(param_combinations) > 20:
        print(f"\n⚠️  Aviso: {len(param_combinations)} combinações podem levar bastante tempo!")
    
    results = []
    
    print("\n" + "-" * 70)
    for i, (max_depth, n_estimators, learning_rate) in enumerate(param_combinations, 1):
        print(f"\n[{i}/{len(param_combinations)}] Testando: max_depth={max_depth}, "
              f"n_estimators={n_estimators}, learning_rate={learning_rate}")
        
        # Treinar modelo com esses parâmetros
        model, encoder, X_test, y_test, X_train, y_train = train_model(
            X, y,
            max_depth=max_depth,
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            test_size=test_size,
            random_state=random_state,
            verbose=False
        )
        
        # Avaliar
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"   Acurácia: {accuracy:.4f} ({accuracy*100:.2f}%)")
        
        # Armazenar resultado
        results.append({
            'max_depth': max_depth,
            'n_estimators': n_estimators,
            'learning_rate': learning_rate,
            'accuracy': accuracy,
            'model': model,
            'encoder': encoder,
            'X_test': X_test,
            'y_test': y_test
        })
    
    # Ordenar por acurácia (melhor primeiro)
    results.sort(key=lambda x: x['accuracy'], reverse=True)
    
    # Exibir top 5 resultados
    print("\n" + "=" * 70)
    print("📊 RESULTADOS DO GRID SEARCH")
    print("=" * 70)
    print("\nTop 5 configurações:")
    print("-" * 70)
    
    for i, result in enumerate(results[:5], 1):
        print(f"\n#{i} - Acurácia: {result['accuracy']:.4f} ({result['accuracy']*100:.2f}%)")
        print(f"     max_depth={result['max_depth']}, "
              f"n_estimators={result['n_estimators']}, "
              f"learning_rate={result['learning_rate']}")
    
    # Melhor modelo
    best_result = results[0]
    print("\n" + "=" * 70)
    print("🏆 MELHOR CONFIGURAÇÃO ENCONTRADA")
    print("=" * 70)
    print(f"Acurácia: {best_result['accuracy']:.4f} ({best_result['accuracy']*100:.2f}%)")
    print(f"Parâmetros:")
    print(f"  max_depth: {best_result['max_depth']}")
    print(f"  n_estimators: {best_result['n_estimators']}")
    print(f"  learning_rate: {best_result['learning_rate']}")
    
    best_params = {
        'max_depth': best_result['max_depth'],
        'n_estimators': best_result['n_estimators'],
        'learning_rate': best_result['learning_rate']
    }
    
    return best_result['model'], best_result['encoder'], best_params, results


if __name__ == '__main__':
    print("=" * 70)
    print("🚀 TREINAMENTO DO MODELO XGBOOST")
    print("   Classificação de Tipos de Pedra")
    print("=" * 70)
    
    # Parsear argumentos
    args = parse_arguments()
    
    # Validar argumentos
    if not validate_arguments(args):
        sys.exit(1)
    
    # Carregar dados
    print("\n📂 Carregando dados...")
    X, y = load_data_for_training()
    
    # Modo Grid Search
    if args.grid_search:
        # Parsear ranges
        max_depth_range = parse_range(args.max_depth_range, int) if args.max_depth_range else [args.max_depth]
        n_estimators_range = parse_range(args.n_estimators_range, int) if args.n_estimators_range else [args.n_estimators]
        learning_rate_range = parse_range(args.learning_rate_range, float) if args.learning_rate_range else [args.learning_rate]
        
        # Executar grid search
        model, encoder, best_params, all_results = run_grid_search(
            X, y,
            max_depth_range=max_depth_range,
            n_estimators_range=n_estimators_range,
            learning_rate_range=learning_rate_range,
            test_size=args.test_size,
            random_state=args.random_state
        )
        
        # Re-treinar o melhor modelo para obter X_test e y_test
        model, encoder, X_test, y_test, X_train, y_train = train_model(
            X, y,
            max_depth=best_params['max_depth'],
            n_estimators=best_params['n_estimators'],
            learning_rate=best_params['learning_rate'],
            test_size=args.test_size,
            random_state=args.random_state,
            verbose=False
        )
        
        # Avaliar melhor modelo
        print("\n" + "=" * 70)
        print("📈 Avaliação Detalhada do Melhor Modelo")
        print("=" * 70)
        metrics = evaluate_model(model, encoder, X_test, y_test)
        
        # Mostrar importância das features
        print_feature_importance(model, X.columns.tolist())
        
        # Salvar apenas o melhor modelo
        if not args.no_save:
            save_model_artifacts(
                model, encoder, X.columns.tolist(), 
                save_enabled=True, 
                suffix='_gridsearch'
            )
    
    # Modo Treino Único (padrão)
    else:
        # Treinar com parâmetros fornecidos
        model, encoder, X_test, y_test, X_train, y_train = train_model(
            X, y,
            max_depth=args.max_depth,
            n_estimators=args.n_estimators,
            learning_rate=args.learning_rate,
            test_size=args.test_size,
            random_state=args.random_state,
            verbose=True
        )
        
        # Avaliar o modelo
        metrics = evaluate_model(model, encoder, X_test, y_test)
        
        # Mostrar importância das features
        print_feature_importance(model, X.columns.tolist())
        
        # Salvar artefatos
        save_model_artifacts(
            model, encoder, X.columns.tolist(), 
            save_enabled=not args.no_save
        )
    
    print("\n" + "=" * 70)
    print("✅ TREINAMENTO CONCLUÍDO!")
    print("=" * 70)
