
# delete tmp directory
rm -rf /workdir-tmp

# create tmp directory
mkdir /workdir-tmp

# copy all files from /SUT to tmp directory
cp -r /SUT/* /workdir-tmp

cp -r /svHelpers/* /workdir-tmp

# cd into tmp directory
cd /workdir-tmp

# ignore files from previous run
rm ./*.json
rm ./*.pdf

# compile all the java files
javac *.java

TARGET=Test

render_graphs(){
  EXTRACT_TARGETS=$(find . -type f -name "*.java" -and -not -name "Verifier.java")
  for EXTRACT_TARGET in ${EXTRACT_TARGETS[@]};
  do
    EXTRACT_TARGET=$(basename $EXTRACT_TARGET .java)
    TARGET_FILTER="\["$EXTRACT_TARGET"\."
    FILE_NAMES=$(ls graal_dumps/*/ | grep SubstrateHostedCompilation | grep $TARGET_FILTER)
    DIR_NAME=$(ls graal_dumps)
    for FILE_NAME in ${FILE_NAMES[@]};
    do
      OUT_FILE=$(echo $FILE_NAME | grep -oP '\[.*?\]' | grep -oP '\[\K[^(]+(?=\()')
      seafoam "graal_dumps/$DIR_NAME/$FILE_NAME:0" render --out $OUT_FILE.pdf
      bgv2json "graal_dumps/$DIR_NAME/$FILE_NAME" > $OUT_FILE.json
    done
  done
}

# dump graph for test method and Test class
#native-image -H:Dump=:1 -H:MaximumInliningSize=0 -H:+UnlockExperimentalVMOptions -H:MethodFilter=org_example_Test org_example_Test
native-image -ea -H:Dump=:1 -H:MaximumInliningSize=0 -H:+UnlockExperimentalVMOptions $TARGET
# rm -rf PointsToAnalysisMethod*

render_graphs

if [[ -z $(grep '[^[:space:]]' *.json) ]]; then
  ORANGE='\033[0;33m'
  NC='\033[0m'
  echo -e "${ORANGE}Could not create graph, retrying with O0${NC}"
  rm -r graal_dumps/*
  native-image -ea -O0 -H:Dump=:1 -H:MaximumInliningSize=0 -H:+UnlockExperimentalVMOptions $TARGET
  render_graphs
fi

# copy graph.json and graph.pdf to /SUT
cp ./*.json /SUT
cp ./*.pdf /SUT
#cp *.class /SUT