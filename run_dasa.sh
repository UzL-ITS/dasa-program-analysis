#!/bin/bash

pushd "$(dirname "$0")" > /dev/null
source .venv_svcomp/bin/activate
# Check if the '-v' argument is among the arguments, indicating that the user wants to see the version
property_no_runtime=0
for arg in "$@"; do
  case "$arg" in
    -v|--version)
      printf '0.1'
      exit 0
      ;;
    *properties/no-runtime-exception.prp) # we don't want to participate here
      property_no_runtime=1
      ;;
  esac
done

if [ "$property_no_runtime" -eq 1 ]; then
  echo "DASA_VERDICT: UNKNOWN" # do this after the check so that version has higher priority
  exit 0
fi

rm -rf ./SUT/
mkdir SUT
# get last argument
last_path="${@: -1}"

# get second last argument
second_last_path="${*: -2:1}"

# check if there is a Main.java in last_path
if [ -f "$second_last_path/Main.java" ]; then
    # switch the last two arguments
    set -- "${@:1:$(($#-2))}" "$last_path" "$second_last_path"
fi

# Loop through all provided paths and copy Java files
for path in "$@"; do
  if [ -d "$path" ]; then
    # Find all Java files in the path
    find "$path" -type f -name "*.java" -exec cp {} ./SUT/ \;
    echo "Java files from $path copied successfully to ./SUT/"
  elif [ -f "$path" ] && [[ "$path" == *.java ]]; then
    # If the argument is a single Java file, copy it
    cp "$path" ./SUT/
    echo "File $path copied successfully to ./SUT/"
  fi
done

pathadd() { # little helper function to add something to the path if it's it not already there
    if [ -d "$1" ] && [[ ":$PATH:" != *":$1:"* ]]; then
        PATH="$1${PATH:+":$PATH"}"
    fi
}

# add graalvm, ruby and graphviz to PATH (needed for seafoam)
GRAALVM_PATH="$(pwd)/libs/graalvm-community-openjdk-22.0.2+9.1/bin"
#RUBY_PATH="$(pwd)/libs/ruby/bin"
#export RUBYLIB="$(pwd)/libs/ruby/lib/ruby/3.4.0:$(pwd)/libs/ruby/lib/ruby/3.4.0/x86_64-linux"
#export GEM_HOME="$(pwd)/libs/ruby/lib/gems.3.4.0"
#export GEM_PATH="$(pwd)/libs/ruby/lib/gems.3.4.0"
export PYTHONPATH="$(pwd)/.venv_svcomp/lib/python3.12/site-packages:$PYTHONPATH"
#GRAPHVIZ_PATH="$(pwd)/libs/graphviz/bin/"
pathadd $GRAALVM_PATH
#pathadd $RUBY_PATH
#pathadd $GRAPHVIZ_PATH

# prepare a working directory to compile the target and create the graph
TMP_WORKDIR="dasa-tmp-workdir"
rm -rf $TMP_WORKDIR > /dev/null
mkdir $TMP_WORKDIR
cp -r ./SUT/* $TMP_WORKDIR
cp -r ./svHelpers/evaluation/* $TMP_WORKDIR

pushd $TMP_WORKDIR > /dev/null

javac ./*.java # compile everything for GraalVM to analyze

render_graphs(){
  EXTRACT_TARGETS=$(find . -type f -name "*.java" -and -not -name "Verifier.java")
  for EXTRACT_TARGET in ${EXTRACT_TARGETS[@]};
  do
    EXTRACT_TARGET=$(basename $EXTRACT_TARGET .java)
    TARGET_FILTER="\["$EXTRACT_TARGET"\."
    FILE_NAMES=$(ls graal_dumps/*/ | grep SubstrateHostedCompilation | grep $TARGET_FILTER)
    DIR_NAME=$(ls graal_dumps)
    WORKDIR_ABS="$(pwd)"
    pushd ../libs/seafoam/bin > /dev/null
    for FILE_NAME in ${FILE_NAMES[@]};
    do
      OUT_FILE=$(echo $FILE_NAME | grep -oP '\[.*?\]' | grep -oP '\[\K[^(]+(?=\()')
      #ruby seafoam "$WORKDIR_ABS/graal_dumps/$DIR_NAME/$FILE_NAME:0" render --out "$WORKDIR_ABS/$OUT_FILE.svg"
      java -jar jruby-complete-10.0.2.0.jar bgv2json "$WORKDIR_ABS/graal_dumps/$DIR_NAME/$FILE_NAME" > "$WORKDIR_ABS/$OUT_FILE.json"
    done
    popd > /dev/null
  done
}

TARGET=Main
# compile the target again with GraalVM to create compiler graphs
#java -Dgraal.Dump=:1 -Dgraal.MaximumInliningSize=0 -Dgraal.MethodFilter=Test.main -XX:CompileCommand=dontinline,Verifier.nondetInt $TARGET

native-image -ea -H:Dump=:1 -H:MaximumInliningSize=0 -H:+UnlockExperimentalVMOptions $TARGET

# extract json graphs out of the compiler graphs using seafoam
render_graphs

# retry with O0 if the json graphs are not available
if [[ -z $(grep '[^[:space:]]' *.json) ]]; then
  ORANGE='\033[0;33m'
  NC='\033[0m'
  echo -e "${ORANGE}Could not create graph, retrying with O0${NC}"
    rm -r graal_dumps/*
    native-image -ea -O0 -H:Dump=:1 -H:MaximumInliningSize=0 -H:+UnlockExperimentalVMOptions $TARGET
    render_graphs
fi

WORKDIR_ABS="$(pwd)"
REWRITE_DIR="$WORKDIR_ABS/rewrite"
mkdir "$REWRITE_DIR"
popd > /dev/null
pushd libs/SVCompRewriter > /dev/null
python3 rewriter.py "$WORKDIR_ABS/" -o "$REWRITE_DIR"
popd > /dev/null
pushd $REWRITE_DIR > /dev/null
javac ./*.java # recompile everything to create a Witness
popd > /dev/null

cp $TMP_WORKDIR/*.json ./SUT/
#cp $TMP_WORKDIR/*.svg ./SUT/
cp $REWRITE_DIR/*.class ./SUT/
cp -r $TMP_WORKDIR/org ./SUT/org

python3 run_sv-comp.py

popd > /dev/null