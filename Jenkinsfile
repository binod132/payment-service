pipeline {
  agent any
  environment {
    REGISTRY="dev-repo.iris.treeleaf.ai"
    GIT_TOKEN = credentials("GIT_TOKENS")
    DOCKER_REGISTRY= credentials("local-registery")
    BRANCH_NAME = "dev"
    REPO_NAME = sh(returnStdout: true, script: 'echo $GIT_URL | awk -F"/" \'{gsub(".git", "", $NF); print $NF}\'').trim()
    SSH_USER=credentials("SSH_USER")
    SSH_IP=credentials("SSH_IP")
    SSH_COMMAND = "cd /home/ubuntu/iris/helm-chart-iris-dev && sh upgrade-dev.sh irisapi"
    IMAGE="python-iris-api:3.10"
  }
  stages {
        stage('Start') {
            steps {
                sh "docker login -u $DOCKER_REGISTRY_USR -p $DOCKER_REGISTRY_PSW ${REGISTRY}"
                echo "Login successfully & starting build with ${BRANCH_NAME}"
              }
            }
        stage('Docker Build') {
            steps {
                sh 'docker build  --no-cache --build-arg  REGISTRY=${REGISTRY} --build-arg  IMAGE=${IMAGE} --build-arg  GIT_TOKEN=${GIT_TOKEN} -f ./Dockerfile -t ${REGISTRY}/${REPO_NAME}:${BRANCH_NAME}  .'
              }
            }
        stage('Docker Push') {
            steps {
                sh 'docker push $REGISTRY/$REPO_NAME:$BRANCH_NAME'
              }
            }
        stage('Clean docker image') {
            steps {
                  sh 'docker rmi $REGISTRY/$REPO_NAME:$BRANCH_NAME'
              }
            }
        stage('deployed to dev server ') {
            steps{
                sshagent(credentials:['ssh_cluster']){
                  sh 'ssh  -o StrictHostKeyChecking=no  $SSH_USER@$SSH_IP $SSH_COMMAND'
                  }
              }
          }
  }
}