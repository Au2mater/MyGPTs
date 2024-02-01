""" test running setup.py in a test environment"""
import os
import shutil
from pathlib import Path
import subprocess
import pytest
from scripts.setup import set_env_variables
import dotenv as de

@pytest.fixture(scope="module", autouse=True)
def test_directory():
    # SETUP / FIXTURES
    main_dir = Path(os.getcwd()) ; print(main_dir)
    # create a temporary folder (%TEMP%/test_MyGPTs) two levels above the current folder
    test_dir = Path(os.getenv("TEMP") or os.getenv("TMPDIR") or "/tmp") / "test_MyGPTs" ; print(test_dir)
    # CLEAN SLATE
    # delete test folder
    # shutil.rmtree(test_dir, ignore_errors=True)
    # delete the MyGPTs_data folder parallel to the test folder
    # shutil.rmtree(test_dir.parent / "MyGPTs_data" , ignore_errors=True)

    # CREATE TEST ENVIRONMENT
    test_dir.mkdir(parents=True, exist_ok=True)
    # copy scripts, src folders and Pipfile to a temporary folder
    # also copy the contents of al the files in the scripts and src folder
    shutil.copytree(src = main_dir /  Path("scripts"), dst= test_dir / "scripts" , dirs_exist_ok=True)
    shutil.copy(src= main_dir / Path("scripts") / "setup.py", dst= test_dir / "scripts" / "setup.py" )
    shutil.copytree(src = main_dir /  Path("src"), dst = test_dir / "src" , dirs_exist_ok=True)
    shutil.copy(src = main_dir / Path("Pipfile"), dst = test_dir / "Pipfile" )
    # open dir in explorer
    # subprocess.Popen(f'explorer "{test_dir}"')
    # change the working directory to the temporary folder
    os.chdir(test_dir) ; print(f'os.getcwd(): {os.getcwd()}')
    # run pipenv install
    subprocess.run("pipenv install", shell=True)
    yield test_dir

    # CLEAN UP / TEAR DOWN
    # remove pipenv virtual environment
    # subprocess.run("pipenv --rm" , shell=True)

    # delete test folder
    # shutil.rmtree(test_dir)

    # delete the MyGPTs_data folder parallel to the test folder
    shutil.rmtree(test_dir.parent / "MyGPTs_data")
    os.chdir(main_dir) ; print(f'os.getcwd(): {os.getcwd()}')


def test_set_env_variables():
    # delete the .env file if it exists
    env_path = Path(".") / ".env"
    if env_path.exists():
        env_path.unlink()
    set_env_variables()
    # check if the .env file exists
    assert env_path.exists() , "The .env file does not exist"
    # load the environment variables from the .env file
    # check that they are read correctly
    assert len(de.dotenv_values(dotenv_path=env_path)) > 0 , "The .env file is empty" 
  

# TESTS
# check that the virtual environment has been created (in %USERPROFILE%/.virtualenvs)
# run pipenv run python scripts/setup.py
def test_run_setup(test_directory):
    setup_path = test_directory / "scripts" / "setup.py"
    subprocess.run(f"pipenv run python  {setup_path}", shell=True)
    # check if the .env file exists
    env_path = Path(".") / ".env" ; print(env_path)
    assert env_path.exists() , "The .env file does not exist"
    # check id the MyGPTs_data folder exists
    data_path = test_directory.parent / "MyGPTs_data" ; print(data_path)
    assert data_path.exists() , "The MyGPTs_data folder does not exist"
    # delete the .env file

