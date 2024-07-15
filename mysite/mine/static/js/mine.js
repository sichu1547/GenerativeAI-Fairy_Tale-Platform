class CellData{
    state = 0;  // flaged, questioned, covered, opened
    property = 0; // 0 - 9 (mine count around cell 0-8/  9 : mine)
    
    getProperty() {
        return this.property;
    }
    setProperty(property){
        this.property = property;
    }
    getState(){
        return this.state;
    }
    setState(state){
        this.state = state;
    }
}
 
class CellModel{
    cells = new Map();
    //셀 초기화 좌표를 key 셀을 value로 매핑
    initCells(){
        for(let row=0; row<rowSize; row++){
            for(let col=0; col<columnSize; col++){
                let key = row+","+col;
                this.cells.set(key, new CellData());
            }
        }
    }
 
    getCellProperty(row, col){
        let key = row+","+col;
        return this.cells.get(key).getProperty();
    }
 
    setCellProperty(row, col, property){
        let key = row+","+col;
        this.cells.get(key).setProperty(property);
    }
 
    getCellState(row, col){
        let key = row+","+col;
        return this.cells.get(key).getState();
    }
 
    setCellState(row, col, state){
        let key = row+","+col;
        this.cells.get(key).setState(state);
    }
    //중복되지 않게 지뢰 숫자만큼 랜덤으로 숫자 뽑기
    getRandomNumbers(){
        let randomNumber = 0;
        const randomNumbers = new Set();
 
        while(randomNumbers.size!=mineCount){
            randomNumber = Math.floor(Math.random()*(rowSize*columnSize));
            randomNumbers.add(randomNumber);
        }
 
        return randomNumbers;
    }
    //랜덤으로 뽑힌 숫자에 해당하는 좌표에 지뢰 심기
    putMine(randomNumbers){
        for(let randomNumber of randomNumbers){
            let row = Math.floor(randomNumber/columnSize);
            let col = randomNumber%columnSize;
            this.setCellProperty(row, col, MINE);
        }
    }
    //지뢰 초기화
    initMine(){
        let randomNumbers = this.getRandomNumbers();
        this.putMine(randomNumbers);
    }
 
    initCellsProperty(){
        for(let row=0; row<rowSize; row++){
            for(let col=0; col<columnSize; col++){
                if(this.getCellProperty(row,col)!=9)
                    this.setCellProperty(row, col, this.getMineCountAroundCell(row,col));
            }
        }
    }
    //주변 셀의 마인 갯수 찾기 ==> property에 값을 넣기 위해
    getMineCountAroundCell(row, col){
        let rowNum = Number(row);
        let colNum = Number(col);
        
        let mineCountAroundCell = 0;
        
        if(colNum>0 && colNum<columnSize-1 && rowNum>0 && rowNum<rowSize-1){
            if(this.getCellProperty(rowNum, colNum+1)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum, colNum-1)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum+1, colNum-1)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum+1, colNum)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum+1, colNum+1)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum-1, colNum-1)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum-1, colNum)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum-1, colNum+1)==MINE)
                mineCountAroundCell++;
        }
        else if(rowNum==0 && colNum==0){
            if(this.getCellProperty(rowNum,colNum+1)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum+1,colNum)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum+1,colNum+1)==MINE)
                mineCountAroundCell++;
        }
        else if(rowNum==0 && colNum==(columnSize-1)){
            if(this.getCellProperty(rowNum,colNum-1)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum+1,colNum)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum+1,colNum-1)==MINE)
                mineCountAroundCell++;
        }
        else if(rowNum==(rowSize-1) && colNum==0){
            if(this.getCellProperty(rowNum,colNum+1)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum-1,colNum)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum-1,colNum+1)==MINE)
                mineCountAroundCell++;
        }
        else if(rowNum==(rowSize-1) && colNum==(columnSize-1)){
            if(this.getCellProperty(rowNum-1,colNum-1)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum-1,colNum)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum,colNum-1)==MINE)
                mineCountAroundCell++;
        }
        else if(colNum==0){
            if(this.getCellProperty(rowNum,colNum+1)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum-1,colNum+1)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum+1,colNum+1)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum-1,colNum)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum+1,colNum)==MINE)
                mineCountAroundCell++;    
        }
        else if(colNum==(columnSize-1)){
            if(this.getCellProperty(rowNum,colNum-1)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum-1,colNum-1)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum+1,colNum-1)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum-1,colNum)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum+1,colNum)==MINE)
                mineCountAroundCell++;    
        }
        else if(rowNum==0){
            if(this.getCellProperty(rowNum+1,colNum+1)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum+1,colNum)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum+1,colNum-1)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum,colNum-1)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum,colNum+1)==MINE)
                mineCountAroundCell++;    
        }
        else if(rowNum==(rowSize-1)){
            if(this.getCellProperty(rowNum-1,colNum-1)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum-1,colNum)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum-1,colNum+1)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum,colNum-1)==MINE)
                mineCountAroundCell++;
            if(this.getCellProperty(rowNum,colNum+1)==MINE)
                mineCountAroundCell++;    
        }
        return mineCountAroundCell;
    }
 
    newGame(){
        this.initCells();
        this.initMine();
        this.initCellsProperty();
    }
 
}
 
class Presenter{
    cellModel = new CellModel();
    newGame(){
        this.cellModel.newGame();
        $('.cells').css('pointer-events','auto');
        // 지뢰찾기 마우스 클릭 불가능하게 설정
    }
    
    //마우스 좌우 동시클릭시 사용할 메소드
    //셀 주변의 깃발 갯수를 반환한다.
    getAroundFlagedCellCount(row, col){
        let rowNum = Number(row);
        let colNum = Number(col);
        // 타입을 정해주지 않아서 에러 발생했음
 
        let flagedCellCount = 0;
        
        if(this.isFlagedCell(rowNum+1, colNum+1))
            flagedCellCount++;
        if(this.isFlagedCell(rowNum+1, colNum))
            flagedCellCount++;
        if(this.isFlagedCell(rowNum+1, colNum-1))
            flagedCellCount++;
        if(this.isFlagedCell(rowNum, colNum+1))
            flagedCellCount++;
        if(this.isFlagedCell(rowNum, colNum-1))
            flagedCellCount++;
        if(this.isFlagedCell(rowNum-1, colNum+1))
            flagedCellCount++;
        if(this.isFlagedCell(rowNum-1, colNum))
            flagedCellCount++;
        if(this.isFlagedCell(rowNum-1, colNum-1))
            flagedCellCount++;
 
        return flagedCellCount;
    }
    
    //깃발이 꽂혀있으면 true 반환
    isFlagedCell(row, col){
        if(row>=0 && col>=0 && row<rowSize && col<columnSize){
            if(this.cellModel.getCellState(row, col) == FLAGED)
                return true;
            else
                return false;
        }
    }
 
    //마우스 좌우 동시클릭 주변8칸 오픈
    checkAroundCells(row, col){
        let rowNum = Number(row);
        let colNum = Number(col);
        if(this.cellModel.getCellProperty(rowNum, colNum) == this.getAroundFlagedCellCount(rowNum, colNum))
            {
                this.checkSingleCell(rowNum+1, colNum+1);
                this.checkSingleCell(rowNum+1, colNum);
                this.checkSingleCell(rowNum+1, colNum-1);
                this.checkSingleCell(rowNum, colNum+1);
                this.checkSingleCell(rowNum, colNum-1);
                this.checkSingleCell(rowNum-1, colNum+1);
                this.checkSingleCell(rowNum-1, colNum);
                this.checkSingleCell(rowNum-1, colNum-1);
            }
    }
    //마우스 왼쪽 클릭시 셀 확인
    checkSingleCell(row, col){
        let rowNum = Number(row);
        let colNum = Number(col);
        if((colNum>=0) && (rowNum>=0) && (rowNum<rowSize) && (colNum<columnSize)){
            let state = this.cellModel.getCellState(rowNum, colNum);
            if(state == COVERED){
                let property = this.cellModel.getCellProperty(rowNum, colNum);
                if(property == MINE){
                    this.gameOver();
                }
                else if(property==0){
                    this.openCell(rowNum, colNum);
                    this.checkSingleCell(rowNum+1,colNum+1);
                    this.checkSingleCell(rowNum+1,colNum);
                    this.checkSingleCell(rowNum+1,colNum-1);
                    this.checkSingleCell(rowNum,colNum+1);
                    this.checkSingleCell(rowNum,colNum-1);
                    this.checkSingleCell(rowNum-1,colNum+1);
                    this.checkSingleCell(rowNum-1,colNum);
                    this.checkSingleCell(rowNum-1,colNum-1);
                }
                else
                    this.openCell(rowNum, colNum);
            }
            else if(state == OPENED)
                return;
            else if(state == QUESTIONED)
                return;
            else if(state == FLAGED)
                return;
 
            if(this.isVictory()){
                this.clearMessage();
                timerStop();
            }
        }
        else
            return;
    }
    //승리 확인
    isVictory(){
        let isVictory = false;
        let opendCell = 0;
        let flagedCell = 0;
        for(let row=0; row<rowSize; row++){
            for(let col=0; col<columnSize; col++){
                if(this.cellModel.getCellState(row, col) == OPENED)
                    opendCell++;
                else if(this.cellModel.getCellState(row, col) == FLAGED)
                    flagedCell++;
            }
        }
 
        if(opendCell + flagedCell == rowSize*columnSize){
            isVictory=true;
        }
        return isVictory;
    }
    //셀 오픈
    openCell(row, col){
        this.cellModel.setCellState(row, col, OPENED);
        let property = this.cellModel.getCellProperty(row, col);
        $('.row'+row+".col"+col).css('height','100%');
        $('.row'+row+".col"+col).css('width','100%');
        $('.row'+row+".col"+col).css('border','1px solid var(--black-color)');
 
        if(property==0){
            $('.row'+row+".col"+col).css('background-color','var(--grey-light-color)');
        }
        else{
            if(property==1)
                $('.row'+row+".col"+col).css('color','blue');
            else if(property==2)
                $('.row'+row+".col"+col).css('color','green');
            else if(property==3)    
                $('.row'+row+".col"+col).css('color','red');
            else if(property==4)
                $('.row'+row+".col"+col).css('color','violet');
            else if(property==5)    
                $('.row'+row+".col"+col).css('color','magenta');
            else
                $('.row'+row+".col"+col).css('color','black');
 
            $('.row'+row+".col"+col).text(property);
        }
    }
    //패배
    gameOver(){
        for(let row=0; row<rowSize; row++){
            for(let col=0; col<columnSize; col++){
                if(this.cellModel.getCellProperty(row, col)==MINE){
                    $('.cell.row'+row+".col"+col).empty();
                    $('.cell.row'+row+".col"+col).append('<i class="fas fa-bomb fa"></i>');
                    $('.cell.row'+row+".col"+col).css('background-color','red');
                    $('.cell.row'+row+".col"+col).css('border','4px solid var(--red-color');
                }
            }
        }
        $('.cells').css('pointer-events','none');
        timerStop();
    }
    //클리어시 함수 호출
    clearMessage(){
        for(let row=0; row<rowSize; row++){
            for(let col=0; col<columnSize; col++){
                if(this.cellModel.getCellProperty(row, col)==MINE){
                    $('.cell.row'+row+".col"+col).empty();
                    $('.cell.row'+row+".col"+col).append('<i class="fas fa-child fa"></i>');
                    $('.cell.row'+row+".col"+col).css('background-color','blue');
                    $('.cell.row'+row+".col"+col).css('background-color','white');
                    $('.cell.row'+row+".col"+col).css('border','4px solid white');
                }
            }
        }
    }
    //마우스 좌클릭
    leftClicked(row, col){
        this.checkSingleCell(row, col); 
    }
    //마우스 우클릭
    rightClicked(row, col){
        if(this.cellModel.getCellState(row, col)==FLAGED){
            this.changeCoveredState(row,col);
        }
        else if(this.cellModel.getCellState(row, col)==COVERED){
            this.changeFlagedState(row,col);
            if(this.isVictory()){
                this.clearMessage();
                timerStop();
            }
        }
        else{
            return;
        }
    }
    //스크롤 클릭
    scrollClicked(row, col){
        if(this.cellModel.getCellState(row, col)==QUESTIONED){
            this.changeCoveredState(row,col);
        }
        else if(this.cellModel.getCellState(row, col)==COVERED){
            this.changeQuestionedState(row,col);
        }
        else{
            return;
        }
    }
    //cell의 state를 flaged로 바꾼다.
    changeFlagedState(row, col){
        this.cellModel.setCellState(row, col, FLAGED);
        $('.cell.row'+row+".col"+col).append('<div style="color:red;"> <i class="fas fa-flag fa"></i></div>');
    }
    //cell의state를 questioned로 바꾼다.
    changeQuestionedState(row, col){
        this.cellModel.setCellState(row, col, QUESTIONED);
        $('.cell.row'+row+".col"+col).append('<div style="color:blue;"> <i class="fas fa-question fa"></i></div>');
    }
    //cell의state를 uncovered로 바꾼다.
    changeCoveredState(row, col){
        this.cellModel.setCellState(row, col, COVERED);
        $('.cell.row'+row+".col"+col).empty();
    }
 
}
 
const presenter = new Presenter();
 
let MINE = 9;       
let COVERED = 0;
let OPENED = 1;
let FLAGED = 2;
let QUESTIONED = 3;
 
let rowSize = 10;
let columnSize = 8;
let mineCount = 10;
 
let time = 0;
let timerOn = false;
 
let leftClicked = false;
let rightClicked = false;
 
//난이도 선택
function selectDifficulty(e){
    let difficulty = $(e.target).text();
    newGame(difficulty);
    $('.difficultyLevelSelectionButton').css('border','none');
    $(e.target).css('border','2px solid black');
}
//게임 생성
function newGame(difficulty){
    setGameProperties(difficulty);
    presenter.newGame();
    makeCellHTMLTags();
    timerReStart();
}
//cell에 해당하는 HTML에 태그 생성
function makeCellHTMLTags() {
    let cellTags = "";
    $('.cells').empty();
    for(let row=0; row<rowSize; row++){
        for(let col=0; col<columnSize; col++){
            cellTags+="<div class=\"cell row"+row+" col"+col+"\"></div>";
        }
    }
    $('.cells').append(cellTags);
}
//난이도에 따른 프로퍼티 설정
function setGameProperties(difficulty){
    if(difficulty=='easy'){
        rowSize=10;
        columnSize=8;
        mineCount=10;
        $('.cells').css('grid-auto-columns', '30px');
        $('.cells').css('grid-auto-rows', '30px');
    }
    else if(difficulty=='normal'){
        rowSize=18;
        columnSize=14;
        mineCount=40;
        $('.cells').css('grid-auto-columns', '27px');
        $('.cells').css('grid-auto-rows', '27px');
    }
    else if(difficulty=='hard'){
        rowSize=24;
        columnSize=20;
        mineCount=89;
        $('.cells').css('grid-auto-columns', '24px');
        $('.cells').css('grid-auto-rows', '24px');
    }
    else{
 
    }
}
//마우스 눌렸을 때
function mouseDown(e){
    let row;
    let col;
    if($(e.target).attr('class').split(' ')[0]!='cell'){
        row = $(e.target.parentElement.parentElement).attr('class').split(' ')[1].substr(3,4);
        col = $(e.target.parentElement.parentElement).attr('class').split(' ')[2].substr(3,4);
    }
    else{
        row = $(e.target).attr('class').split(' ')[1].substr(3,4);
        col = $(e.target).attr('class').split(' ')[2].substr(3,4);
    }
    
    if(e.button==0){
        leftClicked = true;
        presenter.leftClicked(row,col);
    }
    else if(e.button==1){
        presenter.scrollClicked(row, col);
    }
    else{
        rightClicked = true;
        presenter.rightClicked(row, col);
    }
 
    if(leftClicked&&rightClicked)
        presenter.checkAroundCells(row,col);
}
//마우스 뗄 때
function mouseUp(e){
    if(e.button==0)
        leftClicked = false;
    if(e.button==2)
        rightClicked = false;
}
//타이머 재시작
function timerReStart(){
    time = 0;
    timerOn=true;
}
//타이머 스탑
function timerStop(){
    timerOn=false;
}
//타이머 실행
function timer(){
    setTimeout(()=>{
        if(timerOn==true)
            time++;
    timer();},1000);
    $('.timer').text(time);
}
 
$(document).ready(function(){
    $('.cells').on('contextmenu',() => false);
    $('.difficultyLevelSelectionWindow').on('click',(e)=>selectDifficulty(e));
    $('.cells').on('mousedown', (e) => mouseDown(e));
    $('.cells').on('mouseup', (e) => mouseUp(e));
    $('.newGame').on('click', () => newGame());
    newGame();
    timer();
})
