# AiCEE
AiCEE

How to install dependance modules
step 1: 使用 pip 安裝 Pipenv （也可以使用 Homebrew）
$ pip install pipenv

step 2: 建立 python 3 的環境
$ pipenv --three

step 3: 

會根據執行的 python 指令，決定是否使用需你的環境 （不進入虛擬環境中）
λ pipenv run python run.py

或者
進入虛擬環境中，類似於 “source venv/bin/activate”
$ pipenv shell
